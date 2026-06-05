# import sys
# from pathlib import Path
# ETL_ROOT = Path(__file__).resolve().parents[1]
# if str(ETL_ROOT) not in sys.path:
#     sys.path.insert(0, str(ETL_ROOT))

from moduly.utils import hash_do_wsad_json, sklej_warunki_w_WHERE
from moduly.db_core import utworz_engine_do_db
from moduly.ai_modele import llm_quest_summary
from moduly.ai_prompty_misje import get_quest_summary
from moduly.ai_logi import (
    create_logs,
    save_ai_logs_to_db
)

from sqlalchemy import text
import time


def _extract_answer_text(answer) -> str:
    content = answer.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") in {None, "text", "output_text"}:
                text_value = block.get("text")
                if text_value:
                    return str(text_value).strip()

    return str(content or "").strip()


def generate_and_save_quest_summary(
        silnik, 
        llm,
        kraina: str | None = None, 
        fabula: str | None = None, 
        dodatek: str | None = None, 
        id_misji: int | None = None
) -> dict[int, str]:
    print(
        "--- Start generowania podsumowan misji "
        f"(kraina={kraina!r}, fabula={fabula!r}, dodatek={dodatek!r}, id_misji={id_misji!r})"
    )

    try:
        q_select_misja_hash = text(f"""
            WITH MAIN AS (
                SELECT 
                    M.MISJA_ID_MOJE_PK, M.MISJA_ID_Z_GRY, ZM.HTML_SKOMPRESOWANY,
                    ROW_NUMBER() OVER (PARTITION BY M.MISJA_ID_MOJE_PK ORDER BY DATA_WYSCRAPOWANIA DESC) AS RNK
                FROM dbo.MISJE AS M
                INNER JOIN dbo.ZRODLO_MISJE AS ZM
                    ON M.MISJA_ID_MOJE_PK = ZM.MISJA_ID_MOJE_FK
                WHERE 1=1
                AND NOT EXISTS (
                                SELECT 1
                                FROM dbo.MISJE_PODSUMOWANIA AS MP
                                WHERE MP.MISJA_ID_MOJE_FK = M.MISJA_ID_MOJE_PK
                                )
                                   
                {sklej_warunki_w_WHERE(
                    kraina=kraina,
                    fabula=fabula,
                    dodatek=dodatek,
                    id_misji=id_misji
                )}
            )

            SELECT MISJA_ID_MOJE_PK, MISJA_ID_Z_GRY, HTML_SKOMPRESOWANY
            FROM MAIN
            WHERE RNK = 1
        """)
    except Exception as e:
        print(f"--- Blad budowania zapytania SELECT: {e}")
        raise

    q_insert_summary = text("""
        INSERT INTO dbo.MISJE_PODSUMOWANIA (
            MISJA_ID_MOJE_FK,
            MISJA_ID_Z_GRY,
            PODSUMOWANIE
        )
        SELECT
            :misja_id_moje_fk,
            :misja_id_z_gry,
            :podsumowanie
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.MISJE_PODSUMOWANIA
            WHERE MISJA_ID_MOJE_FK = :misja_id_moje_fk
        )
    """)

    try:
        with silnik.connect() as conn:
            lista_krotek = conn.execute(q_select_misja_hash, {
                "fabula_en": fabula,
                "kraina_en": kraina,
                "dodatek_en": dodatek,
                "id_misji": id_misji
            }).all()
        print(f"--- Pobrano misje do podsumowania: {len(lista_krotek)}")
    except Exception as e:
        print(f"--- Blad pobierania misji z bazy: {e}")
        raise


    summary = {}
    misje_id_z_gry = {}
    for numer, (misja_id, misja_id_z_gry, html_skompresowany) in enumerate(lista_krotek, start=1):
        started_at = time.perf_counter()
        print(f"--- [{numer}/{len(lista_krotek)}] Misja {misja_id}: start")

        try:
            tresc_misji = hash_do_wsad_json(html_skompresowany)
            answer = get_quest_summary(llm=llm, mission=tresc_misji)
            podsumowanie = _extract_answer_text(answer)

            logs = create_logs(
                raw_response=answer,
                llm=llm,
                misja_id_moje_fk=misja_id,
                stage="quest_summary",
                duration_ms=round((time.perf_counter() - started_at) * 1000),
                input_chars=len(tresc_misji),
                output_chars=len(podsumowanie)
            )
            save_ai_logs_to_db(silnik=silnik, logs=logs)
            summary[misja_id] = podsumowanie
            misje_id_z_gry[misja_id] = misja_id_z_gry
            print(f"--- [{numer}/{len(lista_krotek)}] Misja {misja_id}: OK, znaki={len(podsumowanie)}")
        except Exception as e:
            print(f"--- [{numer}/{len(lista_krotek)}] Misja {misja_id}: BLAD - {e}")
            continue

    parametry_insert = [
            {
                "misja_id_moje_fk": misja_id,
                "misja_id_z_gry": misje_id_z_gry[misja_id],
                "podsumowanie": podsumowanie
            }
            for misja_id, podsumowanie in summary.items()
    ]

    if not parametry_insert:
        print("--- Brak podsumowan do zapisania.")
        return summary

    try:
        with silnik.begin() as conn:
            conn.execute(q_insert_summary, parametry_insert)
        print(f"--- Zapisano nowe podsumowania, prob zapisu: {len(parametry_insert)}")
    except Exception as e:
        print(f"--- Blad zapisu podsumowan do bazy: {e}")
        raise

    print("--- Koniec generowania podsumowan misji.")
    return summary