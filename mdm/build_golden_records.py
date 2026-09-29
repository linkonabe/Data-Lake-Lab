import pandas as pd
import duckdb

DB_PATH = "beverage_lakehouse/dev.duckdb"


def main():
    matches = pd.read_csv("mdm/match_results.csv")
    con = duckdb.connect(DB_PATH)
    companies = con.execute("select * from companies").df()

    # Only asserted (non-abstained) matches become golden-record links —
    # abstentions are deliberately routed to manual review, not silently merged
    confident_matches = matches[matches["matched_company_number"].notna()].copy()

    golden = confident_matches.merge(
        companies,
        left_on="matched_company_number",
        right_on="company_number",
        how="left",
    )

    golden_records = golden[[
        "company_number", "company_name", "postcode",
        "vendor_record_id", "vendor_company_name", "match_score",
    ]].rename(columns={
        "vendor_record_id": "source_vendor_record_id",
        "vendor_company_name": "source_vendor_name_variant",
    })

    golden_records.to_csv("mdm/golden_records.csv", index=False)

    # Write back to DuckDB too, so this becomes queryable alongside `companies`
    con.execute("CREATE OR REPLACE TABLE golden_records AS SELECT * FROM golden_records")
    con.close()

    print(f"Golden records created: {len(golden_records)}")
    print(f"Records requiring manual review (abstained): {len(matches) - len(golden_records)}")
    print(golden_records.head(5).to_string())


if __name__ == "__main__":
    main()
