from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_HOST = "172.22.192.191"  # update to your current WSL2 IP
COLLECTION_NAME = "companies"
MODEL_NAME = "all-MiniLM-L6-v2"


def search(query: str, top_k: int = 5):
    model = SentenceTransformer(MODEL_NAME)
    client = QdrantClient(host=QDRANT_HOST, port=6333)

    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    ).points

    for r in results:
        print(f"[{r.score:.3f}] {r.payload['company_name']}")
        print(f"        {r.payload['text']}")
        print()

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "whisky distillery in Scotland"
    print(f"Query: {query}\n")
    search(query)
