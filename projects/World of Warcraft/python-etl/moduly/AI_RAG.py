from pathlib import Path
import uuid

import yaml
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from moduly.ai_prompty_RAG import get_questions_lore


FOLDER = Path("C:/____Moje-MOJE/MyProjects_4Fun/projects/World of Warcraft/rag-pliki/02_chunki")
COLLECTION_NAME = "wow_lore_chunks"
MODEL_NAME = "BAAI/bge-large-en-v1.5"
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-12-v2"
VECTOR_SIZE = 1024
# BGE: dokumenty/passage bez prefiksu, instrukcja doklejana tylko do query
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
QDRANT_URL = "http://localhost:6333"
RETRIEVE_TOP = 50  # ilu kandydatów z dense retrievalu trafia do rerankera (etap 1)
RERANK_TOP = 5     # ile zwracam po rerankingu (etap 2)
EMBED_BATCH = 128
UPSERT_BATCH = 128


def get_records(folder: Path = FOLDER) -> list[dict]:
    records = []

    for path in sorted(folder.rglob("*.md")):
        text = path.read_text(encoding="utf-8")

        if not text.startswith("---"):
            raise ValueError(f"Missing front matter in file: {path}")

        parts = text.split("---", maxsplit=2)

        if len(parts) < 3:
            raise ValueError(f"Invalid front matter structure in file: {path}")

        front_matter = parts[1].strip()
        body = parts[2].strip()

        metadata = yaml.safe_load(front_matter) or {}

        chunk_id = metadata.get("chunk_id")
        chunk_title = metadata.get("chunk_title")

        if not chunk_id:
            raise ValueError(f"Missing chunk_id in file: {path}")

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
        }
        for point in results.points
    ]


def upsert_points(client: QdrantClient, points: list[PointStruct], batch_size: int = UPSERT_BATCH) -> None:
    for i in range(0, len(points), batch_size):
        client.upsert(collection_name=COLLECTION_NAME, points=points[i:i + batch_size])


def load_reranker(model_name: str = RERANK_MODEL) -> TextCrossEncoder:
    return TextCrossEncoder(model_name=model_name)


def rerank(query: str, candidates: list[dict], reranker: TextCrossEncoder) -> list[dict]:
    # Reranker dostaje surowy query — BEZ instrukcji BGE (ms-marco jej nie zna).
    documents = [candidate["embedding_text"] for candidate in candidates]
    scores = reranker.rerank(query, documents)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    return sorted(candidates, key=lambda candidate: candidate["rerank_score"], reverse=True)[:RERANK_TOP]


def _main_index():
    """Odpalać rzadko i tylko ręcznie, gdy zmienią się chunki."""
    client = load_client()
    reset_collection(client)
    model = load_model()
    records = get_records()
    embeddings = get_embeddings(records, model)
    upsert_points(client, build_points(records, embeddings))


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
