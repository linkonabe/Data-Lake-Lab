# Week 1 — Data Lake Foundation: Outcome & Skills Log

## What was built
- Local S3-compatible object storage (MinIO) running in Docker, with raw/processed
  bucket separation — the foundational pattern of a data lakehouse.
- A real ingestion pipeline: pulled the UK Companies House bulk dataset (850,000
  companies), filtered against real SIC industry codes down to a business-relevant
  subset (1,559 beverage/alcohol manufacturing and wholesale companies), and landed
  the result in object storage programmatically via the MinIO Python client.
- All debugged through genuine infrastructure friction — WSL2 IP drift breaking
  connectivity, missing system packages (`python3.14-venv`), container state loss on
  restart — resolved through methodical diagnosis rather than guesswork.

## Skills acquired, mapped to Lead AI & Data Engineer job requirements

| Job posting language | What I can now demonstrate |
|---|---|
| "cloud data-platform modernization... datalakehouse patterns" | Working lakehouse storage pattern (raw/processed separation) on S3-compatible storage |
| "data pipelines... using Python, SQL, APIs" | Python ingestion script: read, filter, transform, upload — the ELT "E" and part of "T" |
| "integrating data from SaaS platforms... source systems" | Practiced pulling from an external public data source into a platform — same pattern as any SaaS API integration |
| "engineering excellence... observability, reliability" | Methodical failure diagnosis: container status → IP check → port check, rather than guessing |

## AWS transferability
MinIO is S3-API-compatible — the `put_object` calls written here would work almost
unchanged against real AWS S3 using `boto3`. The raw-bucket → processed-bucket pattern
is exactly how production S3 data lakes are structured. The pattern transfers directly,
not just the tool.

## Open gaps (by design, addressed in later weeks)
- No SQL transformation layer yet (dbt — Week 2)
- No data quality checks yet (Week 2)
- No MDM/match-merge exercise yet (Week 3)
- No AI/RAG layer yet (Week 4)

Week 1 proves reliable data ingestion into a lakehouse. It does not yet prove
modeling, cleaning, or querying capability — that's the next three weeks.
