import duckdb
import pandas as pd
import random
import string

random.seed(42)  # reproducible corruption, so results are consistent across reruns

DB_PATH = "beverage_lakehouse/dev.duckdb"


def corrupt_name(name: str) -> str:
    """Simulate how a different system might record the same company name."""
    name = name.strip()

    # Common real-world variations, applied randomly
    if random.random() < 0.4:
        name = name.replace("LIMITED", "LTD").replace("Limited", "Ltd")
    if random.random() < 0.3:
        name = name.title()  # inconsistent casing between systems
    if random.random() < 0.2:
        name = name.replace(",", "").replace(".", "")  # punctuation stripped
    if random.random() < 0.15 and len(name) > 5:
        # simulate a single-character typo
        pos = random.randint(0, len(name) - 1)
        name = name[:pos] + random.choice(string.ascii_uppercase) + name[pos + 1:]
    if random.random() < 0.1:
        name = f"  {name}  "  # stray whitespace, a very common real issue

    return name


def main():
    con = duckdb.connect(DB_PATH)
    companies = con.execute(
        "select company_number, company_name, postcode from companies"
    ).df()
    con.close()

    # Sample 300 companies to represent in our fake "vendor system"
    sample = companies.sample(n=300, random_state=42).copy()

    sample["vendor_company_name"] = sample["company_name"].apply(corrupt_name)
    sample["vendor_postcode"] = sample["postcode"]  # kept accurate — postcode is our blocking key
    sample = sample.rename(columns={"company_number": "true_company_number"})

    vendor_records = sample[
        ["vendor_company_name", "vendor_postcode", "true_company_number"]
    ].reset_index(drop=True)
    vendor_records.insert(0, "vendor_record_id", range(1, len(vendor_records) + 1))

    vendor_records.to_csv("mdm/vendor_records.csv", index=False)
    print(f"Generated {len(vendor_records)} synthetic vendor records")
    print(vendor_records.head(10).to_string())


if __name__ == "__main__":
    main()
