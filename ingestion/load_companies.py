import pandas as pd
from minio import Minio
from minio.error import S3Error
import io

# --- Config ---
MINIO_ENDPOINT = "172.22.192.191:9000"  # your WSL2 IP, S3 API port
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "minioadmin123"
BUCKET_NAME = "raw-data"
SOURCE_CSV = "/home/linkonabe/ai-lab/data-lake-lab/download/BasicCompanyData-2026-08-01-part1_7.csv"

# SIC codes: beverage manufacturing + alcohol wholesale
TARGET_SIC_CODES = {"11010", "11020", "11050", "11060", "46342"}

# Companies House splits SIC codes across 4 columns per company
SIC_COLUMNS = [
    "SICCode.SicText_1",
    "SICCode.SicText_2",
    "SICCode.SicText_3",
    "SICCode.SicText_4",
]


def matches_target_sic(row) -> bool:
    """Check if any of a company's up-to-4 SIC codes match our target list.
    SicText fields look like '11010 - Distilling...', so we match on the
    numeric prefix rather than requiring an exact string match.
    """
    for col in SIC_COLUMNS:
        value = row.get(col)
        if pd.notna(value):
            code = str(value).split(" ")[0].strip()
            if code in TARGET_SIC_CODES:
                return True
    return False


def main():
    print(f"Reading {SOURCE_CSV} ...")
    df = pd.read_csv(SOURCE_CSV, low_memory=False)
    print(f"Loaded {len(df):,} total companies")

    filtered = df[df.apply(matches_target_sic, axis=1)]
    print(f"Filtered to {len(filtered):,} beverage/alcohol-related companies")

    # Convert filtered dataframe to CSV bytes in memory — no need to write
    # a temp file to disk, we can stream straight into MinIO
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    csv_buffer = io.BytesIO(csv_bytes)

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,  # local dev, no TLS
    )

    object_name = "companies_house/beverage_alcohol_companies.csv"
    try:
        client.put_object(
            BUCKET_NAME,
            object_name,
            data=csv_buffer,
            length=len(csv_bytes),
            content_type="text/csv",
        )
        print(f"Uploaded to s3://{BUCKET_NAME}/{object_name}")
    except S3Error as e:
        print(f"MinIO upload failed: {e}")
        raise


if __name__ == "__main__":
    main()
