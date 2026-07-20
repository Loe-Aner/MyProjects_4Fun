from pathlib import Path
import asyncio
import json
import os
import re
import time
import uuid

from sqlalchemy import text

import yaml
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from moduly.ai_prompty_RAG import get_questions_lore, CONST_RULES_CHUNKER
from moduly.ai_modele import llm_chunker
from moduly.ai_logi import create_logs, save_ai_logs_to_db
from moduly.db_core import utworz_engine_do_db


FOLDER = Path("C:/____Moje-MOJE/MyProjects_4Fun/projects/World of Warcraft/rag-pliki/02_chunki")
COLLECTION_NAME = "wow_lore_chunks"
MODEL_NAME = "BAAI/bge-large-en-v1.5"
RERANK_MODEL = "BAAI/bge-reranker-base"
VECTOR_SIZE = 1024
# BGE: dokumenty/passage bez prefiksu, instrukcja doklejana tylko do query
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
QDRANT_URL = "http://localhost:6333"
RETRIEVE_TOP = 100  # ilu kandydatow z dense retrievalu trafia do rerankera (etap 1)
                    # 100 zamiast 50: baza rosnie (50k->100k+), bi-encoder spycha trafne
                    # chunki nizej. Reranker (mocne ogniwo) + prog >0 chronia przed szumem.
RERANK_TOP = 8     # ile zwracam po rerankingu (etap 2)
EMBED_BATCH = 100  # 200+ crashowalo sterownik
UPSERT_BATCH = 128
EMBED_PARALLEL = None
EMBED_PROVIDERS = ["DmlExecutionProvider", "CPUExecutionProvider"]


def repair_quoted_yaml_scalars(front_matter: str) -> str:
    repaired_lines = []

    for line in front_matter.splitlines():
        match = re.match(r'^(\s*[\w-]+:\s*)"(.*)"(\s*)$', line)

        if not match:
            repaired_lines.append(line)
            continue

        prefix, value, suffix = match.groups()
        repaired_lines.append(f'{prefix}"{value.replace(chr(34), chr(92) + chr(34))}"{suffix}')

    return "\n".join(repaired_lines)


def load_front_matter(front_matter: str, path: Path) -> dict:
    try:
        return yaml.safe_load(front_matter) or {}
    except yaml.YAMLError:
        try:
            return yaml.safe_load(repair_quoted_yaml_scalars(front_matter)) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML front matter in file: {path}") from exc


def get_records(folder: Path = FOLDER, document_ids: set[str] | None = None) -> list[dict]:
    records = []
    skipped_invalid = 0

    for path in sorted(folder.rglob("chk_*.md")):
        text = path.read_text(encoding="utf-8")

        if not text.startswith("---"):
            if document_ids is not None:
                skipped_invalid += 1
                continue

            raise ValueError(f"Missing front matter in file: {path}")

        parts = text.split("---", maxsplit=2)

        if len(parts) < 3:
            if document_ids is not None:
                skipped_invalid += 1
                continue

            raise ValueError(f"Invalid front matter structure in file: {path}")

        front_matter = parts[1].strip()
        body = parts[2].strip()

        try:
            metadata = load_front_matter(front_matter, path)
        except ValueError:
            if document_ids is not None:
                skipped_invalid += 1
                continue

            raise

        chunk_id = metadata.get("chunk_id")
        document_id = metadata.get("document_id")
        chunk_title = metadata.get("chunk_title")

        if not chunk_id:
            raise ValueError(f"Missing chunk_id in file: {path}")

        if not document_id:
            raise ValueError(f"Missing document_id in file: {path}")

        if document_ids is not None and document_id not in document_ids:
            continue

        if not chunk_title:
            if document_ids is not None:
                print(f"Qdrant RAG: pomijam (brak chunk_title, stary chunk): {path}")
                skipped_invalid += 1
                continue

            raise ValueError(f"Missing chunk_title in file: {path}")

        embedding_text = f"{chunk_title}\n{body}"

        record = {
            "id": chunk_id,
            "payload": metadata,
            "embedding_text": embedding_text,
            "source_path": str(path),
        }

        records.append(record)

    if skipped_invalid:
        print(f"Qdrant RAG: skipped invalid chunk files: {skipped_invalid}")

    return records


def _ostrzez_jesli_brak_dml() -> None:
    import onnxruntime as ort

    dostepne = ort.get_available_providers()

    if "DmlExecutionProvider" not in dostepne:
        print(
            "UWAGA: DmlExecutionProvider NIEDOSTEPNY - embedding poleci na CPU (cichy fallback)!\n"
            f"       Dostepne providery: {dostepne}\n"
            "       Napraw: odinstaluj onnxruntime, zainstaluj onnxruntime-directml."
        )
    else:
        print("Qdrant RAG: DmlExecutionProvider OK - embedding na iGPU (DirectML).")


def load_model(model_name: str = MODEL_NAME) -> TextEmbedding:
    _ostrzez_jesli_brak_dml()
    return TextEmbedding(model_name=model_name, providers=EMBED_PROVIDERS)


def get_embeddings(
    records: list[dict],
    model: TextEmbedding,
) -> list:
    # BGE: dokumenty bez żadnego prefiksu - goły tekst.
    documents = [record["embedding_text"] for record in records]

    return list(model.embed(documents, batch_size=EMBED_BATCH))


def load_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def create_collection_if_not_exists(client: QdrantClient) -> None:
    if client.collection_exists(collection_name=COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


def reset_collection(client: QdrantClient) -> None:
    # Usuwa kolekcję i tworzy ją od nowa — używać przy zmianie modelu embeddingów.
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)

    create_collection_if_not_exists(client)


def build_points(records: list[dict], embeddings: list) -> list[PointStruct]:
    if len(records) != len(embeddings):
        raise ValueError(
            f"Records and embeddings length mismatch: "
            f"{len(records)} records vs {len(embeddings)} embeddings"
        )

    points = []

    for record, embedding in zip(records, embeddings):
        chunk_id = record["id"]
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))

        payload = record["payload"].copy()
        payload["embedding_config"] = {
            "embedding_model": MODEL_NAME,
            "embedding_dim": VECTOR_SIZE,
            "query_instruction": QUERY_INSTRUCTION,
        }
        payload["embedding_text"] = record["embedding_text"]
        payload["source_path"] = record["source_path"]

        point = PointStruct(
            id=point_id,
            vector=list(embedding),
            payload=payload,
        )

        points.append(point)

    return points


def query_to_embedding(query: str, model: TextEmbedding) -> list[float]:
    # BGE: do query doklejam instrukcję (bez dwukropka jak w e5).
    embedded_query = model.embed([f"{QUERY_INSTRUCTION}{query}"])
    return list(next(embedded_query))


def get_data_from_rag(client: QdrantClient, query: str, model: TextEmbedding):
    query_vector = query_to_embedding(query, model)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=RETRIEVE_TOP,
        with_payload=True,
    )

    return [
        {
            "id": point.id,
            "score": round(point.score, 3),
            "chunk_title": point.payload["chunk_title"],
            "embedding_text": point.payload["embedding_text"],
            "chunk_id": point.payload.get("chunk_id"),
            "document_id": point.payload.get("document_id"),
        }
        for point in results.points
    ]


def upsert_points(client: QdrantClient, points: list[PointStruct], batch_size: int = UPSERT_BATCH) -> None:
    for i in range(0, len(points), batch_size):
        client.upsert(collection_name=COLLECTION_NAME, points=points[i:i + batch_size])


def delete_document_points(client: QdrantClient, document_id: str) -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )
        ),
        wait=True,
    )


def get_pending_qdrant_documents(silnik, include_already_upserted: bool = False) -> list[dict]:
    already_upserted_filter = ""

    if not include_already_upserted:
        already_upserted_filter = """
        AND NOT EXISTS (
            SELECT 1
            FROM dbo.ZRODLO_QDRANT AS zq
            WHERE zq.DOC_ID = zr.DOC_ID
                AND zq.BODY_HASH = zr.BODY_HASH
                AND zq.STATUS = 'upserted'
                AND zq.EMBEDDING_MODEL = :embedding_model
                AND zq.COLLECTION_NAME = :collection_name
        )
        """

    q_select_records = text(f"""
        WITH latest AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY DOC_ID
                    ORDER BY DATA_WYSCRAPOWANIA DESC, TECH_ID DESC
                ) AS rn
            FROM dbo.ZRODLO_RAG
            WHERE STATUS IN ('created', 'updated')
        )

        SELECT zr.TECH_ID, zr.DOC_ID, zr.BODY_HASH, zr.STATUS
        FROM latest AS zr
        WHERE zr.rn = 1
        {already_upserted_filter};
    """)

    with silnik.connect() as conn:
        return conn.execute(
            q_select_records,
            {
                "embedding_model": MODEL_NAME,
                "collection_name": COLLECTION_NAME,
            },
        ).mappings().all()


def save_qdrant_log(
    silnik,
    doc_id: str,
    body_hash: str,
    status: str,
    chunk_count: int | None = None,
    error_message: str | None = None,
) -> None:
    if status == "upserted":
        q_insert_log = text("""
            IF NOT EXISTS (
                SELECT 1
                FROM dbo.ZRODLO_QDRANT
                WHERE DOC_ID = :doc_id
                  AND BODY_HASH = :body_hash
                  AND STATUS = 'upserted'
                  AND EMBEDDING_MODEL = :embedding_model
                  AND COLLECTION_NAME = :collection_name
            )
            BEGIN
                INSERT INTO dbo.ZRODLO_QDRANT (
                    DOC_ID,
                    BODY_HASH,
                    STATUS,
                    EMBEDDING_MODEL,
                    COLLECTION_NAME,
                    ILE_CHUNKOW,
                    ERROR_MESSAGE
                )
                VALUES (
                    :doc_id,
                    :body_hash,
                    :status,
                    :embedding_model,
                    :collection_name,
                    :chunk_count,
                    :error_message
                );
            END
        """)
    else:
        q_insert_log = text("""
            INSERT INTO dbo.ZRODLO_QDRANT (
                DOC_ID,
                BODY_HASH,
                STATUS,
                EMBEDDING_MODEL,
                COLLECTION_NAME,
                ILE_CHUNKOW,
                ERROR_MESSAGE
            )
            VALUES (
                :doc_id,
                :body_hash,
                :status,
                :embedding_model,
                :collection_name,
                :chunk_count,
                :error_message
            );
        """)

    with silnik.begin() as conn:
        conn.execute(
            q_insert_log,
            {
                "doc_id": doc_id,
                "body_hash": body_hash,
                "status": status,
                "embedding_model": MODEL_NAME,
                "collection_name": COLLECTION_NAME,
                "chunk_count": chunk_count,
                "error_message": error_message,
            },
        )


def load_reranker(model_name: str = RERANK_MODEL) -> TextCrossEncoder:
    return TextCrossEncoder(model_name=model_name, providers=EMBED_PROVIDERS)


def rerank(query: str, candidates: list[dict], reranker: TextCrossEncoder) -> list[dict]:
    documents = [candidate["embedding_text"] for candidate in candidates]
    scores = reranker.rerank(query, documents)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    return sorted(candidates, key=lambda candidate: candidate["rerank_score"], reverse=True)[:RERANK_TOP]


def embed_and_upsert(
    client: QdrantClient,
    silnik,
    records: list[dict],
    todo_docs: list[dict],
    model: TextEmbedding,
    completed_docs: set[str],
    batch_size: int = EMBED_BATCH,
    upsert_batch: int = UPSERT_BATCH,
) -> None:
    body_hash_by_doc = {doc["DOC_ID"]: doc["BODY_HASH"] for doc in todo_docs}

    remaining_by_doc: dict[str, int] = {}
    for record in records:
        doc_id = record["payload"]["document_id"]
        remaining_by_doc[doc_id] = remaining_by_doc.get(doc_id, 0) + 1
    total_by_doc = dict(remaining_by_doc)

    texts = [record["embedding_text"] for record in records]
    embed_iter = model.embed(texts, batch_size=batch_size, parallel=EMBED_PARALLEL)

    buffer: list[tuple[dict, list]] = []

    def flush() -> None:
        if not buffer:
            return

        recs = [rec for rec, _ in buffer]
        embs = [emb for _, emb in buffer]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=build_points(recs, embs),
        )

        for rec in recs:
            doc_id = rec["payload"]["document_id"]
            remaining_by_doc[doc_id] -= 1

            if remaining_by_doc[doc_id] == 0:
                save_qdrant_log(
                    silnik,
                    doc_id=doc_id,
                    body_hash=body_hash_by_doc[doc_id],
                    status="upserted",
                    chunk_count=total_by_doc[doc_id],
                )
                completed_docs.add(doc_id)
                print(f"{doc_id}=upserted ({total_by_doc[doc_id]} chunks)")

        buffer.clear()

    for record, embedding in zip(
        records,
        tqdm(embed_iter, total=len(records), desc="Qdrant RAG embedding", unit="chunk"),
    ):
        buffer.append((record, embedding))

        if len(buffer) >= upsert_batch:
            flush()

    flush()


def insert_into_qdrant_collection(reset: bool = False):
    """"""
    silnik = utworz_engine_do_db()
    client = load_client()

    if reset:
        reset_collection(client)
    else:
        create_collection_if_not_exists(client)

    todo_docs = get_pending_qdrant_documents(
        silnik,
        include_already_upserted=reset,
    )

    if not todo_docs:
        print("Qdrant RAG: no documents to index")
        return

    print(f"Qdrant RAG: documents to index: {len(todo_docs)}")

    docs_by_id = {doc["DOC_ID"]: doc for doc in todo_docs}
    document_ids = set(docs_by_id)
    records = get_records(document_ids=document_ids)

    records_by_doc_id: dict[str, list[dict]] = {
        document_id: [] for document_id in document_ids
    }

    for record in records:
        records_by_doc_id[record["payload"]["document_id"]].append(record)

    for doc in todo_docs:
        doc_id = doc["DOC_ID"]
        body_hash = doc["BODY_HASH"]

        if not records_by_doc_id[doc_id]:
            save_qdrant_log(
                silnik,
                doc_id=doc_id,
                body_hash=body_hash,
                status="error",
                error_message=f"No chunks found for DOC_ID={doc_id}",
            )
            print(f"{doc_id}=error (no chunks found)")

    records = [
        record
        for doc_records in records_by_doc_id.values()
        for record in doc_records
    ]

    if not records:
        print("Qdrant RAG: no chunks found for selected documents")
        return

    if not reset:
        for doc in todo_docs:
            if doc["STATUS"] != "updated":
                continue

            doc_id = doc["DOC_ID"]
            body_hash = doc["BODY_HASH"]
            delete_document_points(client, doc_id)
            print(f"{doc_id}=deleted_old")
            save_qdrant_log(
                silnik,
                doc_id=doc_id,
                body_hash=body_hash,
                status="deleted_old",
            )

    model = load_model()
    completed_docs: set[str] = set()

    try:
        print(f"Qdrant RAG: embedding chunks: {len(records)}")
        embed_and_upsert(client, silnik, records, todo_docs, model, completed_docs)
    except Exception as exc:
        for doc in todo_docs:
            doc_id = doc["DOC_ID"]

            if doc_id in completed_docs:
                continue  # doc juz w Qdrancie i oznaczony 'upserted' — nie loguj bledu

            doc_records = records_by_doc_id[doc_id]

            if not doc_records:
                continue

            save_qdrant_log(
                silnik,
                doc_id=doc_id,
                body_hash=doc["BODY_HASH"],
                status="error",
                chunk_count=len(doc_records),
                error_message=str(exc),
            )
            print(f"{doc_id}=error")

        raise


def load_rag_components():
    return load_client(), load_model(), load_reranker()


def get_candidates(query: str, client, model, reranker):
    candidates = get_data_from_rag(client, query, model)
    return rerank(query, candidates, reranker)


def get_filtered_candidates(llm, misje_tekst) -> str:
    """
    Tworzy zbiór z odsianymi chunkami. Zbudowany jest z krotek: tytuł oraz tekst.
    """

    client, model, reranker = load_rag_components()
    questions = get_questions_lore(llm, misje_tekst)
    
    cands = dict()
    for i, question in enumerate(questions):
        candidates = get_candidates(question.question, client, model, reranker)

        filtered_candidates = [
            candidate
            for candidate in candidates
            if candidate.get("rerank_score", 0) > 0 # ====== wstepne zalozenie ======
        ]

        cands[i+1] = {
            "question": question.question,
            "candidates": filtered_candidates
        }

    cands = {
        key: value
        for key, value in cands.items()
        if value["candidates"] # wyrzucam te chunki, ktore zwrocily pusta liste
    }

    rag_context_chunks = []

    for record in cands.values():
        question = record["question"]

        for candidate in record["candidates"]:
            title = candidate["chunk_title"]
            embedding_text = candidate["embedding_text"]

            rag_context_chunks.append({
                "question": question,
                "title": title,
                "answer": embedding_text,
            })
    return "\n\n".join(
        f"### Pytanie: {chunk['question']}\n"
        f"### Tytuł: {chunk['title']}\n"
        f"### Odpowiedź:\n{chunk['answer']}"
        for chunk in rag_context_chunks
    ) # type: ignore


def _wyciagnij_tekst_z_ai_message(msg: AIMessage) -> str:
    content = msg.content

    if isinstance(content, str):
        return content

    fragmenty = []

    for blok in content:
        if isinstance(blok, str):
            fragmenty.append(blok)
        elif isinstance(blok, dict) and blok.get("type") in ("text", "output_text"):
            fragmenty.append(blok.get("text", ""))

    return "".join(fragmenty)


_ZNAKI_KONTROLNE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_NIELEGALNE_W_NAZWIE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _usun_znaki_kontrolne(tekst: str) -> str:
    return _ZNAKI_KONTROLNE.sub("", tekst)


def _odescapuj_jesli_literalne(tresc: str) -> str:
    if "\n" not in tresc and "\\n" in tresc:
        tresc = tresc.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    return tresc


def _przecytuj_wartosc_yaml(wartosc: str) -> str:
    if len(wartosc) >= 2 and wartosc[0] == wartosc[-1] and wartosc[0] in ("'", '"'):
        wnetrze = wartosc[1:-1]
        if wartosc[0] == "'":
            wnetrze = wnetrze.replace("\\'", "'").replace("''", "'")
    else:
        wnetrze = wartosc

    wnetrze = wnetrze.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{wnetrze}"'


def _napraw_yaml(front_matter: str) -> str:
    naprawione = []

    for linia in front_matter.splitlines():
        m_map = re.match(r'^(\s*)("?[A-Za-z_][\w-]*"?)\s*:\s+(\S.*?)\s*$', linia)
        m_list = re.match(r"^(\s*)-\s+(\S.*?)\s*$", linia)

        if m_map:
            wciecie, klucz, wartosc = m_map.groups()
            klucz = klucz.strip('"')
            if re.fullmatch(r"-?\d+", wartosc):
                naprawione.append(f"{wciecie}{klucz}: {wartosc}")
            else:
                naprawione.append(f"{wciecie}{klucz}: {_przecytuj_wartosc_yaml(wartosc)}")
        elif m_list:
            wciecie, wartosc = m_list.groups()
            naprawione.append(f"{wciecie}- {_przecytuj_wartosc_yaml(wartosc)}")
        else:
            naprawione.append(linia)

    wynik = "\n".join(naprawione)

    if front_matter.endswith("\n"):
        wynik += "\n"

    return wynik


def _bezpieczna_nazwa_pliku(chunk_id: str) -> str:
    nazwa = _NIELEGALNE_W_NAZWIE.sub("", chunk_id).strip()
    return nazwa[:180]


def _slug(tekst: str) -> str:
    tekst = tekst.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "_", tekst).strip("_")


def _zapewnij_chunk_id(front_matter: str, chunk_id: str) -> str:
    if re.search(r"(?m)^\s*chunk_id\s*:", front_matter):
        return front_matter

    nowa_linia = f'chunk_id: "{chunk_id}"\n'
    linie = front_matter.splitlines(keepends=True)
    wynik = []
    wstawiono = False

    for linia in linie:
        wynik.append(linia)
        if not wstawiono and re.match(r"^\s*document_id\s*:", linia):
            wynik.append(nowa_linia)
            wstawiono = True

    if not wstawiono:
        wynik.insert(0, nowa_linia)

    return "".join(wynik)


def _zapisz_chunki_z_json(raw: str, sciezka_dokumentu: str) -> tuple[int, list[str]]:
    chunks = json.loads(raw)
    folder_zapis = Path(sciezka_dokumentu.replace("01_dokumenty", "02_chunki"))

    if not chunks:
        folder_zapis.mkdir(parents=True, exist_ok=True)
        (folder_zapis / "_brak_lore.md").write_text(
            "Model nie wygenerowal zadnego chunka - dokument bez tresci lore.\n",
            encoding="utf-8",
        )
        return 0, []

    zapisane = 0
    bledy_chunkow: list[str] = []

    for nr_chunka, tresc_chunka in chunks.items():
        try:
            if not isinstance(tresc_chunka, str) or not tresc_chunka.strip():
                raise ValueError("wartosc chunka nie jest niepustym stringiem")

            tresc_chunka = _odescapuj_jesli_literalne(tresc_chunka)
            tresc_chunka = _usun_znaki_kontrolne(tresc_chunka)

            czesci = tresc_chunka.split("---", 2)
            if len(czesci) < 3:
                raise ValueError("brak struktury ---frontmatter---body")
            _, front_matter, body = czesci

            try:
                yfm = yaml.safe_load(front_matter)
            except yaml.YAMLError:
                if "\\n" in front_matter:
                    front_matter = (
                        front_matter.replace("\\r\\n", "\n")
                        .replace("\\n", "\n")
                        .replace("\\t", "\t")
                    )
                front_matter = _napraw_yaml(front_matter)
                yfm = yaml.safe_load(front_matter)

            if not isinstance(yfm, dict):
                raise ValueError("frontmatter nie sparsowal sie do slownika")

            document_id = yfm["document_id"]
            chunk_idx = int(yfm.get("chunk_index", nr_chunka))
            chunk_id = yfm.get("chunk_id")

            if not chunk_id or "\n" in str(chunk_id):
                suffix = yfm.get("topic") or _slug(str(yfm.get("chunk_title", ""))) or f"chunk_{chunk_idx}"
                chunk_id = document_id.replace("doc_", "chk_", 1) + "_" + suffix
                front_matter = _zapewnij_chunk_id(front_matter, chunk_id)

            docnum = document_id.rsplit("_", 1)[1]
            nazwa_chunka = _bezpieczna_nazwa_pliku(
                chunk_id.replace(f"_{docnum}_", f"_{chunk_idx:03d}_", 1)
            )
            if not nazwa_chunka:
                raise ValueError("pusta nazwa pliku po sanityzacji")

            tresc_do_zapisu = f"---{front_matter}---{body}"
            sciezka_zapis = folder_zapis / f"{nazwa_chunka}.md"
            sciezka_zapis.parent.mkdir(parents=True, exist_ok=True)
            sciezka_zapis.write_text(tresc_do_zapisu, encoding="utf-8")
            zapisane += 1

        except Exception as exc:
            bledy_chunkow.append(f"chunk {nr_chunka}: {type(exc).__name__}: {exc}")

    return zapisane, bledy_chunkow


async def _przetworz_dokument(sciezka_dokumentu, llm, llm_bound, sem, silnik, db_lock, bledy):
    async with sem:
        plik_md = next(Path(sciezka_dokumentu).glob("*.md"), None)

        if plik_md is None:
            print(f"Chunker: brak .md w {sciezka_dokumentu}")
            return

        try:
            tresc = plik_md.read_text(encoding="utf-8")
            messages = [
                SystemMessage(content=CONST_RULES_CHUNKER),
                HumanMessage(content=tresc),
            ]

            start = time.perf_counter()
            msg = await llm_bound.ainvoke(messages)
            duration_ms = int((time.perf_counter() - start) * 1000)

            raw = _wyciagnij_tekst_z_ai_message(msg)

            parsing_error = None
            try:
                zapisane, bledy_chunkow = _zapisz_chunki_z_json(raw, str(sciezka_dokumentu))

                if zapisane == 0 and not bledy_chunkow:
                    print(f"Chunker OK {plik_md.name}: 0 chunków (brak lore — zapisano _brak_lore.md)")
                else:
                    print(f"Chunker OK {plik_md.name}: {zapisane} chunków")

                if bledy_chunkow:
                    parsing_error = f"{len(bledy_chunkow)} bledow chunkow: " + " | ".join(bledy_chunkow)
                    for blad_chunka in bledy_chunkow:
                        bledy.append((str(plik_md), blad_chunka))
                    print(f"Chunker CHUNK ERRORS {plik_md.name}: {len(bledy_chunkow)} bledow, zapisane {zapisane}")
            except Exception as exc:
                parsing_error = f"{type(exc).__name__}: {exc}"
                bledy.append((str(plik_md), parsing_error))
                print(f"Chunker PARSE ERROR {plik_md}: {parsing_error}")

            log = create_logs(
                raw_response=msg,
                llm=llm,
                misja_id_moje_fk=None,
                input_chars=len(tresc),
                output_chars=len(raw),
                stage="rag_chunking",
                duration_ms=duration_ms,
                parsing_error=parsing_error,
            )

            # Log od razu po skonczonym dokumencie. Blokujacy zapis do DB w watku
            # (zeby nie blokowac petli), serializowany lockiem - insert jest tani.
            try:
                async with db_lock:
                    await asyncio.to_thread(save_ai_logs_to_db, silnik, log)
            except Exception as exc:
                print(f"Chunker LOG ERROR {plik_md.name}: {type(exc).__name__}: {exc}")

        except Exception as exc:
            blad = f"{type(exc).__name__}: {exc}"
            bledy.append((str(plik_md), blad))
            print(f"Chunker API ERROR {plik_md}: {blad}")


async def wygeneruj_chunki_dla_pustych(max_concurrency: int = 5) -> list[tuple[str, str]]:
    dokumenty = []

    for root, dirs, files in os.walk(FOLDER):
        if not dirs and not files:
            dokumenty.append(root.replace("02_chunki", "01_dokumenty"))

    if not dokumenty:
        print("Chunker: brak pustych folderów do przetworzenia")
        return []

    print(f"Chunker: dokumentów do przetworzenia: {len(dokumenty)} (równolegle: {max_concurrency})")

    silnik = utworz_engine_do_db()
    llm = llm_chunker()
    llm_bound = llm.bind(response_format={"type": "json_object"})
    sem = asyncio.Semaphore(max_concurrency)
    db_lock = asyncio.Lock()

    bledy: list[tuple[str, str]] = []

    await asyncio.gather(*[
        _przetworz_dokument(sciezka, llm, llm_bound, sem, silnik, db_lock, bledy)
        for sciezka in dokumenty
    ])

    print(f"Chunker: zakończono. Nieudane: {len(bledy)} / {len(dokumenty)}")
    return bledy
