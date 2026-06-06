import json
import time

from sqlalchemy import text

from moduly.db_core import utworz_engine_do_db
from moduly.utils import hash_do_wsad_json, sklej_warunki_w_WHERE
from moduly.ai_modele import llm_lore, llm_context
from moduly.ai_prompty_RAG import get_questions_lore_raw, get_context_lore
from moduly.ai_logi import create_logs, save_ai_logs_to_db
from moduly.AI_RAG import (
    COLLECTION_NAME,
    MODEL_NAME,
    load_rag_components,
    get_candidates,
)

# Komunikat dla translatora/redaktora, gdy nie ma prekomputowanego kontekstu.
PLACEHOLDER_BRAK_KONTEKSTU = "Brak kontekstu dla tej misji - pomiń tę sekcję"


_Q_INS_PYTANIE = text("""
    INSERT INTO dbo.MISJE_LORE_PYTANIA (MISJA_ID_MOJE_FK, NR_PYTANIA, ASPEKT, PYTANIE, MODEL)
    VALUES (:misja_id, :nr, :aspekt, :pytanie, :model)
""")

_Q_INS_TRAFIENIE = text("""
    INSERT INTO dbo.MISJE_LORE_TRAFIENIA (
        MISJA_ID_MOJE_FK, NR_PYTANIA, POZYCJA,
        QDRANT_POINT_ID, CHUNK_ID, DOCUMENT_ID,
        SCORE_DENSE, RERANK_SCORE, COLLECTION_NAME, EMBEDDING_MODEL
    )
    VALUES (
        :misja_id, :nr, :pozycja,
        :point_id, :chunk_id, :document_id,
        :score_dense, :rerank_score, :collection, :embedding_model
    )
""")

_Q_INS_KONTEKST = text("""
    INSERT INTO dbo.MISJE_LORE_KONTEKST (MISJA_ID_MOJE_FK, PODSUMOWANIE, MODEL)
    VALUES (:misja_id, :podsumowanie, :model)
""")

_Q_SELECT_KONTEKST = text("""
    SELECT PODSUMOWANIE
    FROM dbo.MISJE_LORE_KONTEKST
    WHERE MISJA_ID_MOJE_FK = :misja_id
""")


def czytaj_kontekst_lore(conn, misja_id: int) -> str:
    """
    Gotowiec dla translatora/redaktora: odczytuje prekomputowane podsumowanie lore.
    Przyjmuje otwarte połączenie (conn) — żeby wpiąć się w istniejącą transakcję ai.py.
    Brak wiersza / pusty tekst -> placeholder do pominięcia w promptcie.
    """
    row = conn.execute(_Q_SELECT_KONTEKST, {"misja_id": misja_id}).first()
    if not row or not row[0] or not str(row[0]).strip():
        return PLACEHOLDER_BRAK_KONTEKSTU
    return str(row[0]).strip()


def _formatuj_chunki(rag_context_chunks: list[dict]) -> str:
    """Ten sam format kontekstu co w AI_RAG.get_filtered_candidates."""
    return "\n\n".join(
        f"### Pytanie: {chunk['question']}\n"
        f"### Tytuł: {chunk['title']}\n"
        f"### Odpowiedź:\n{chunk['answer']}"
        for chunk in rag_context_chunks
    )


def _zbuduj_kontekst_dla_misji(
    silnik,
    misja_id: int,
    wsad_rag: str,
    lore_llm,
    context_llm,
    rag_components,
    nadpisz: bool = True,
) -> tuple[int, int, int]:
    """Pełny przebieg dla jednej misji. Zwraca (liczba_pytan, liczba_trafien, dlugosc_podsumowania)."""
    client, embed_model, reranker = rag_components

    # --- 1) PYTANIA ---
    t0 = time.perf_counter()
    questions, raw_questions = get_questions_lore_raw(lore_llm, wsad_rag)
    save_ai_logs_to_db(silnik, create_logs(
        raw_response=raw_questions,
        llm=lore_llm,
        misja_id_moje_fk=misja_id,
        input_chars=len(wsad_rag),
        output_chars=sum(len(q.question or "") for q in questions),
        stage="rag_questions",
        duration_ms=round((time.perf_counter() - t0) * 1000),
    ))

    # --- 2) RETRIEVAL + RERANK -> ślad + chunki do kontekstu ---
    pytania_rows = []
    trafienia_rows = []
    rag_context_chunks = []

    for nr, q in enumerate(questions, start=1):
        pytania_rows.append({
            "misja_id": misja_id, "nr": nr,
            "aspekt": q.aspect, "pytanie": q.question,
            "model": getattr(lore_llm, "model_name", None),
        })

        kandydaci = get_candidates(q.question, client, embed_model, reranker)
        odsiani = [c for c in kandydaci if c.get("rerank_score", 0) > 0]

        for pozycja, c in enumerate(odsiani, start=1):
            trafienia_rows.append({
                "misja_id": misja_id, "nr": nr, "pozycja": pozycja,
                "point_id": str(c["id"]),
                "chunk_id": c.get("chunk_id"),
                "document_id": c.get("document_id"),
                "score_dense": c.get("score"),
                "rerank_score": c.get("rerank_score"),
                "collection": COLLECTION_NAME,
                "embedding_model": MODEL_NAME,
            })
            rag_context_chunks.append({
                "question": q.question,
                "title": c["chunk_title"],
                "answer": c["embedding_text"],
            })

    rag_context = _formatuj_chunki(rag_context_chunks)

    # --- 3) PODSUMOWANIE LORE ---
    t1 = time.perf_counter()
    context_lore = get_context_lore(context_llm, wsad_rag, rag_context)
    podsumowanie = str(context_lore.content or "").strip()
    save_ai_logs_to_db(silnik, create_logs(
        raw_response=context_lore,
        llm=context_llm,
        misja_id_moje_fk=misja_id,
        input_chars=len(wsad_rag) + len(rag_context),
        output_chars=len(podsumowanie),
        stage="rag_context",
        duration_ms=round((time.perf_counter() - t1) * 1000),
    ))

    # --- 4) ZAPIS (jedna transakcja na misję) ---
    with silnik.begin() as conn:
        if nadpisz:
            for tabela in ("MISJE_LORE_TRAFIENIA", "MISJE_LORE_PYTANIA", "MISJE_LORE_KONTEKST"):
                conn.execute(
                    text(f"DELETE FROM dbo.{tabela} WHERE MISJA_ID_MOJE_FK = :m"),
                    {"m": misja_id},
                )
        if pytania_rows:
            conn.execute(_Q_INS_PYTANIE, pytania_rows)
        if trafienia_rows:
            conn.execute(_Q_INS_TRAFIENIE, trafienia_rows)
        conn.execute(_Q_INS_KONTEKST, {
            "misja_id": misja_id,
            "podsumowanie": podsumowanie,
            "model": getattr(context_llm, "model_name", None),
        })

    return len(questions), len(trafienia_rows), len(podsumowanie)


def _pobierz_misje_bez_kontekstu(silnik, kraina, fabula, dodatek, id_misji) -> list:
    zapytanie = text(f"""
        WITH MAIN AS (
            SELECT
                M.MISJA_ID_MOJE_PK, M.MISJA_ID_Z_GRY, ZM.HTML_SKOMPRESOWANY,
                ROW_NUMBER() OVER (PARTITION BY M.MISJA_ID_MOJE_PK ORDER BY ZM.DATA_WYSCRAPOWANIA DESC) AS RNK
            FROM dbo.MISJE AS M
            INNER JOIN dbo.ZRODLO_MISJE AS ZM
                ON M.MISJA_ID_MOJE_PK = ZM.MISJA_ID_MOJE_FK
            WHERE 1=1
              AND NOT EXISTS (
                  SELECT 1
                  FROM dbo.MISJE_LORE_KONTEKST AS K
                  WHERE K.MISJA_ID_MOJE_FK = M.MISJA_ID_MOJE_PK
              )
              {sklej_warunki_w_WHERE(kraina=kraina, fabula=fabula, dodatek=dodatek, id_misji=id_misji)}
        )
        SELECT MISJA_ID_MOJE_PK, MISJA_ID_Z_GRY, HTML_SKOMPRESOWANY
        FROM MAIN
        WHERE RNK = 1
    """)
    with silnik.connect() as conn:
        return conn.execute(zapytanie, {
            "kraina_en": kraina,
            "fabula_en": fabula,
            "dodatek_en": dodatek,
            "id_misji": id_misji,
        }).all()


def buduj_kontekst_lore(
    fabula: str | None = None,
    dodatek: str | None = None,
    kraina: str | None = None,
    id_misji: int | None = None,
    nadpisz: bool = True,
    tryb: str | None = None,
):
    """
    Prekomputuje kontekst lore dla misji wybranych po fabule i/lub dodatku
    (ew. krainie albo pojedynczym ID). Bierze tylko misje BEZ kontekstu.
    """
    silnik = utworz_engine_do_db(tryb) if tryb else utworz_engine_do_db()

    print(
        "--- Start prekomputacji kontekstu lore "
        f"(kraina={kraina!r}, fabula={fabula!r}, dodatek={dodatek!r}, id_misji={id_misji!r})"
    )
    misje = _pobierz_misje_bez_kontekstu(silnik, kraina, fabula, dodatek, id_misji)
    print(f"--- Misji bez kontekstu do zrobienia: {len(misje)}\n")

    if not misje:
        print("--- Nic do roboty.")
        return

    lore_llm = llm_lore()
    context_llm = llm_context()
    rag_components = load_rag_components()

    sukces = 0
    bledy = 0

    for numer, (misja_id, _misja_id_z_gry, html_skompresowany) in enumerate(misje, start=1):
        if not html_skompresowany:
            print(f"--- [{numer}/{len(misje)}] Misja {misja_id}: brak HTML, pomijam.")
            continue

        try:
            wsad_json = hash_do_wsad_json(html_skompresowany, jezyk="EN")
            wsad_rag = json.dumps(json.loads(wsad_json).get("Misje_EN", {}), indent=4, ensure_ascii=False)

            ile_pytan, ile_trafien, dl_pods = _zbuduj_kontekst_dla_misji(
                silnik, misja_id, wsad_rag,
                lore_llm, context_llm, rag_components,
                nadpisz=nadpisz,
            )
            sukces += 1
            print(f"--- [{numer}/{len(misje)}] Misja {misja_id}: OK "
                  f"(pytania={ile_pytan}, trafienia={ile_trafien}, podsumowanie={dl_pods} zn.)")
        except Exception as e:
            bledy += 1
            print(f"--- [{numer}/{len(misje)}] Misja {misja_id}: BŁĄD - {e}")
            continue

    print(f"\n--- Koniec. Zrobione={sukces}, błędy={bledy}")
