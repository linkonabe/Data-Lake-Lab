import duckdb
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from postcode_regions import region_for_postcode

DB_PATH = "beverage_lakehouse/dev.duckdb"
QDRANT_HOST = "172.22.192.191"  # update to your current WSL2 IP
COLLECTION_NAME = "companies"

# Small, fast, well-established embedding model — good default for a local
# CPU/GPU-light workload, 384-dimensional vectors
MODEL_NAME = "all-MiniLM-L6-v2"


def build_document(row) -> str:
    region = region_for_postcode(row["postcode"])
    return (
        f"{row['company_name']} is a company based in {row['postcode']}, {region}, "
        f"classified under SIC code {row['sic_code_primary']} "
        f"({row['sic_description_primary']}). Status: {row['company_status']}."
    )


def main():
    con = duckdb.connect(DB_PATH)
    companies = con.execute("select * from companies").df()
    con.close()

    print(f"Loading embedding model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    documents = companies.apply(build_document, axis=1).tolist()
    print(f"Embedding {len(documents)} company records...")
    embeddings = model.encode(documents, show_progress_bar=True)

    client = QdrantClient(host=QDRANT_HOST, port=6333)

    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=embeddings.shape[1], distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload={
                "company_number": companies.iloc[i]["company_number"],
                "company_name": companies.iloc[i]["company_name"],
                "text": documents[i],
            },
        )
        for i in range(len(documents))
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Upserted {len(points)} vectors into Qdrant collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
