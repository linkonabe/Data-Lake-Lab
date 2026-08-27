# Data Lake Lab — Project Reproduction Guide (Weeks 1–2)

A local-first data lakehouse pipeline: raw data ingestion into S3-compatible
storage, transformed and tested via dbt-core + DuckDB. Built with zero cloud cost.

## Prerequisites
- Docker + Docker Compose
- Python 3.12+ with `venv`
- ~2GB free disk space (dataset + DuckDB file)

---

## Week 1: Ingestion into a MinIO Lakehouse

### 1. Project structure
```bash
mkdir -p ~/ai-lab/data-lake-lab
cd ~/ai-lab/data-lake-lab
mkdir -p ingestion mdm quality rag docs download
git init
```

### 2. `.gitignore`

pycache/
*.pyc
.env
.venv/
target/
dbt_packages/
logs/
*.duckdb
download/
.direnv/
.envrc
secrete
.vscode/


### 3. MinIO via Docker Compose
`docker-compose.yml`:
```yaml
services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # Web console
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: minioadmin123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  minio_data:
```
```bash
docker compose up -d
```

Create two buckets via the console at `http://<your-wsl2-ip>:9001` (find your IP
with `hostname -I` — WSL2 IPs can drift on restart):
- `raw-data`
- `processed-data`

### 4. Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas minio python-dotenv
```

### 5. Get the source data
Download a UK Companies House "Basic Company Data" bulk CSV part from
`https://download.companieshouse.gov.uk/en_output.html`, extract it into `download/`.

### 6. Ingestion script
`ingestion/load_companies.py`:
```python
import pandas as pd
from minio import Minio
from minio.error import S3Error
import io

MINIO_ENDPOINT = "172.22.192.191:9000"  # update to your current WSL2 IP
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "minioadmin123"
BUCKET_NAME = "raw-data"
SOURCE_CSV = "download/BasicCompanyData-2026-08-01-part1_7.csv"

# Beverage manufacturing + alcohol wholesale SIC codes
TARGET_SIC_CODES = {"11010", "11020", "11050", "11060", "46342"}

SIC_COLUMNS = [
    "SICCode.SicText_1", "SICCode.SicText_2",
    "SICCode.SicText_3", "SICCode.SicText_4",
]


def matches_target_sic(row) -> bool:
    for col in SIC_COLUMNS:
        value = row.get(col)
        if pd.notna(value):
            code = str(value).split(" ")[0].strip()
            if code in TARGET_SIC_CODES:
                return True
    return False


def main():
    df = pd.read_csv(SOURCE_CSV, low_memory=False)
    filtered = df[df.apply(matches_target_sic, axis=1)]

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    csv_buffer = io.BytesIO(csv_bytes)

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    object_name = "companies_house/beverage_alcohol_companies.csv"
    client.put_object(
        BUCKET_NAME, object_name,
        data=csv_buffer, length=len(csv_bytes), content_type="text/csv",
    )
    print(f"Uploaded to s3://{BUCKET_NAME}/{object_name}")


if __name__ == "__main__":
    main()
```
```bash
python ingestion/load_companies.py
```
Result: 850,000 companies scanned → 1,559 beverage/alcohol companies uploaded to
`raw-data/companies_house/beverage_alcohol_companies.csv`.

---

## Week 2: dbt + DuckDB Transformation Layer

### 1. Install dbt
```bash
pip install duckdb dbt-duckdb
```

### 2. Initialize the dbt project
```bash
dbt init beverage_lakehouse   # choose duckdb when prompted
cd beverage_lakehouse
```

### 3. Configure `~/.dbt/profiles.yml` to reach MinIO
```yaml
beverage_lakehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: dev.duckdb
      extensions:
        - httpfs
      settings:
        s3_endpoint: "172.22.192.191:9000"  # update to your current WSL2 IP
        s3_access_key_id: "admin"
        s3_secret_access_key: "minioadmin123"
        s3_use_ssl: false
        s3_url_style: "path"
```
```bash
dbt debug   # confirm "Connection test: [OK connection ok]"
```

### 4. Staging model — raw passthrough
`models/staging/stg_companies.sql`:
```sql
select *
from read_csv_auto('s3://raw-data/companies_house/beverage_alcohol_companies.csv')
```

`models/staging/schema.yml`:
```yaml
version: 2

models:
  - name: stg_companies
    description: "Raw pass-through of beverage/alcohol Companies House records from the raw-data lakehouse bucket."
```

### 5. Marts model — cleaned, filtered, business-ready
`models/marts/companies.sql`:
```sql
with source as (
    select * from {{ ref('stg_companies') }}
),

cleaned as (
    select
        "CompanyName"                           as company_name,
        "CompanyNumber"                         as company_number,
        "CompanyStatus"                         as company_status,
        "RegAddress.AddressLine1"               as address_line_1,
        "RegAddress.PostTown"                   as address_town,
        "RegAddress.PostCode"                   as postcode,
        "IncorporationDate"                     as incorporation_date,
        split_part("SICCode.SicText_1", ' ', 1) as sic_code_primary,
        "SICCode.SicText_1"                     as sic_description_primary
    from source
)

select *
from cleaned
where company_status = 'Active'
-- Excludes 'Active - Proposal to Strike off', 'Liquidation', and
-- 'In Administration' — not stable/useful entities for business analysis.
```

`models/marts/schema.yml`:
```yaml
version: 2

models:
  - name: companies
    description: "Cleaned, business-ready beverage/alcohol manufacturing companies. Excludes non-Active statuses (Liquidation, In Administration, Proposal to Strike Off) as a deliberate data quality decision."
    columns:
      - name: company_number
        description: "Companies House unique identifier."
        tests:
          - unique
          - not_null
      - name: company_name
        tests:
          - not_null
      - name: company_status
        tests:
          - accepted_values:
              values: ['Active']
```

### 6. Build and test
```bash
dbt run
dbt test
```
Result: `stg_companies` (1,559 rows) → `companies` (1,387 active rows), 4/4 tests
passing (uniqueness, completeness, status validation).

---

## Architecture summary

Companies House CSV
↓ (pandas filter by SIC code)
MinIO raw-data bucket (S3-compatible object storage)
↓ (DuckDB httpfs extension, read_csv_auto)
dbt staging model (stg_companies) — raw passthrough
↓ (dbt SQL transformation)
dbt marts model (companies) — cleaned, renamed, filtered to Active
↓ (dbt tests)
Validated, reconciled, business-ready dataset

