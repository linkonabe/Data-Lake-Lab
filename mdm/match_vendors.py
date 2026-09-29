import duckdb
import pandas as pd
from rapidfuzz import fuzz

DB_PATH = "beverage_lakehouse/dev.duckdb"
MATCH_THRESHOLD = 80  # below this, we don't trust the match — flagged as unresolved


def normalize(name: str) -> str:
    """Light normalization before scoring — strips whitespace and standardizes
    common suffixes, so the fuzzy scorer isn't penalized for trivial differences
    it shouldn't have to work hard to see through."""
    name = name.strip().upper()
    name = name.replace("LIMITED", "LTD")
    return name


def main():
    con = duckdb.connect(DB_PATH)
    companies = con.execute(
        "select company_number, company_name, postcode from companies"
    ).df()
    con.close()

    vendors = pd.read_csv("mdm/vendor_records.csv")

    results = []
    for _, vendor in vendors.iterrows():
        # Stage 1: block by exact postcode match
        candidates = companies[companies["postcode"] == vendor["vendor_postcode"]]

        if candidates.empty:
            results.append({
                "vendor_record_id": vendor["vendor_record_id"],
                "vendor_company_name": vendor["vendor_company_name"],
                "matched_company_number": None,
                "matched_company_name": None,
                "match_score": 0,
                "true_company_number": vendor["true_company_number"],
                "asserted_correct": False,
                "abstained": True,
                "best_candidate_was_true_match": False,
            })
            continue

        # Stage 2: fuzzy-score the vendor name against each candidate in the block
        vendor_name_norm = normalize(vendor["vendor_company_name"])
        candidates = candidates.copy()
        candidates["score"] = candidates["company_name"].apply(
            lambda name: fuzz.token_sort_ratio(vendor_name_norm, normalize(name))
        )

        best = candidates.loc[candidates["score"].idxmax()]
        matched_number = best["company_number"] if best["score"] >= MATCH_THRESHOLD else None

        # Track the best candidate regardless of threshold, so we can distinguish
        # "wrong guess" from "correctly abstained but would've been right"
        best_candidate_was_true_match = best["company_number"] == vendor["true_company_number"]

        results.append({
            "vendor_record_id": vendor["vendor_record_id"],
            "vendor_company_name": vendor["vendor_company_name"],
            "matched_company_number": matched_number,
            "matched_company_name": best["company_name"] if matched_number else None,
            "match_score": best["score"],
            "true_company_number": vendor["true_company_number"],
            "asserted_correct": matched_number == vendor["true_company_number"],
            "abstained": matched_number is None,
            "best_candidate_was_true_match": best_candidate_was_true_match,
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv("mdm/match_results.csv", index=False)

    asserted = results_df[~results_df["abstained"]]
    abstained = results_df[results_df["abstained"]]

    false_positives = asserted[~asserted["asserted_correct"]]
    missed_correct_abstentions = abstained[abstained["best_candidate_was_true_match"]]

    print(f"Total records: {len(results_df)}")
    print(f"Asserted a match: {len(asserted)} ({len(asserted)/len(results_df):.1%})")
    print(f"  - Correct:  {asserted['asserted_correct'].sum()}")
    print(f"  - WRONG (false positive): {len(false_positives)}")
    print(f"Abstained (below threshold): {len(abstained)}")
    print(f"  - Of those, best candidate WAS actually correct: {len(missed_correct_abstentions)}")
    print(f"\nPrecision (of asserted matches, % correct): {asserted['asserted_correct'].mean():.1%}")

if __name__ == "__main__":
    main()
