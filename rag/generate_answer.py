import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_HOST = "172.22.192.191"  # update to your current WSL2 IP
COLLECTION_NAME = "companies"
MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

RELEVANCE_THRESHOLD = 0.45  # below this, we don't trust the retrieval enough to answer


def retrieve(query: str, top_k: int = 5):
    model = SentenceTransformer(MODEL_NAME)
    client = QdrantClient(host=QDRANT_HOST, port=6333)
    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    ).points

    return results


def build_prompt(query: str, results) -> str:
    context = "\n".join(f"- {r.payload['text']}" for r in results)
    return f"""You are answering questions about UK beverage and alcohol companies using ONLY the context below.
Do not use any outside knowledge. If the context does not contain enough information to answer, say so explicitly — do not guess or invent details.

Context:
{context}

Question: {query}

Answer, citing specific company names from the context:"""


def generate(query: str):
    results = retrieve(query)

    if not results or results[0].score < RELEVANCE_THRESHOLD:
        print("No sufficiently relevant companies found in the dataset for this query.")
        return

    print("Retrieved context:")
    for r in results:
        print(f"  [{r.score:.3f}] {r.payload['company_name']}")
    print()

    prompt = build_prompt(query, results)

    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
    )
    response.raise_for_status()
    answer = response.json()["response"]

    print(f"Question: {query}\n")
    print(f"Answer:\n{answer}\n")
    print(f"--- Grounded in {len(results)} retrieved records (top score: {results[0].score:.3f}) ---")


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "Tell me about whisky distilleries in Scotland"
    generate(query)
