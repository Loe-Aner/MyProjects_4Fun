from pathlib import Path
import re
import uuid

from sqlalchemy import text

import yaml
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
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

from moduly.ai_prompty_RAG import get_questions_lore
from moduly.db_core import utworz_engine_do_db


FOLDER = Path("C:/____Moje-MOJE/MyProjects_4Fun/projects/World of Warcraft/rag-pliki/02_chunki")
COLLECTION_NAME = "wow_lore_chunks"
MODEL_NAME = "BAAI/bge-large-en-v1.5"
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-12-v2"
VECTOR_SIZE = 1024
# BGE: dokumenty/passage bez prefiksu, instrukcja doklejana tylko do query
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
QDRANT_URL = "http://localhost:6333"
RETRIEVE_TOP = 50  # ilu kandydatów z dense retrievalu trafia do rerankera (etap 1)
RERANK_TOP = 3     # ile zwracam po rerankingu (etap 2)
EMBED_BATCH = 128
UPSERT_BATCH = 128


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

    for path in sorted(folder.rglob("*.md")):
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


def load_model(model_name: str = MODEL_NAME) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)


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
    return TextCrossEncoder(model_name=model_name)


def rerank(query: str, candidates: list[dict], reranker: TextCrossEncoder) -> list[dict]:
    # Reranker dostaje surowy query — BEZ instrukcji BGE (ms-marco jej nie zna).
    documents = [candidate["embedding_text"] for candidate in candidates]
    scores = reranker.rerank(query, documents)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    return sorted(candidates, key=lambda candidate: candidate["rerank_score"], reverse=True)[:RERANK_TOP]


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

    try:
        print(f"Qdrant RAG: embedding chunks: {len(records)}")
        embeddings = get_embeddings(records, model)
        upsert_points(client, build_points(records, embeddings))
    except Exception as exc:
        for doc in todo_docs:
            doc_id = doc["DOC_ID"]
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

    for doc in todo_docs:
        doc_id = doc["DOC_ID"]
        doc_records = records_by_doc_id[doc_id]

        if not doc_records:
            continue

        save_qdrant_log(
            silnik,
            doc_id=doc_id,
            body_hash=doc["BODY_HASH"],
            status="upserted",
            chunk_count=len(doc_records),
        )
        print(f"{doc_id}=upserted ({len(doc_records)} chunks)")


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


# if __name__ == "__main__":
#     query = "who restored the Sunwell"

#     final = get_candidates(query)
#     for item in final:
#         print(item["rerank_score"], item["chunk_title"])
