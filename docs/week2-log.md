# Week 2 — dbt Transformation Layer: Outcome & Skills Log

## What was built
- dbt-core (via dbt-duckdb adapter) wired to MinIO through DuckDB's httpfs extension,
  enabling SQL queries directly against S3-compatible object storage.
- A staging model (`stg_companies`) — raw, unmodified passthrough of the ingested
  Companies House CSV, following the dbt convention of keeping staging free of
  business logic.
- A cleaned mart model (`companies`) — renamed columns, extracted a proper SIC code
  field from a combined code+description string, and filtered to only companies with
  an "Active" status.
- A documented, deliberate business judgment call: companies in Liquidation, In
  Administration, or "Proposal to Strike Off" were excluded as not being stable or
  useful entities for business analysis — recorded as a comment in the model itself,
  not a silent decision.
- Four automated dbt tests (`unique`, `not_null` x2, `accepted_values`) proving data
  quality and reconciliation, not just eyeballing counts once.

## Skills acquired, mapped to Lead AI & Data Engineer job requirements

| Job posting language | What I can now demonstrate |
|---|---|
| "data modeling, quality... reconciliation" | A layered dbt model (staging → marts) with automated tests enforcing uniqueness and completeness |
| "resilient, reusable ETL/ELT pipelines" | A working ELT pattern: extract (ingestion), load (MinIO), transform (dbt/DuckDB) |
| "engineering excellence... code quality, observability" | Documented business logic directly in SQL comments; tests that fail loudly rather than corrupting data silently |
| "translate business problems into... data solutions" | Made and justified a real business judgment call (excluding insolvent/strike-off companies) rather than blindly passing through raw data |

## Real debugging encountered (not just tutorial-following)
- dbt-duckdb's default profile has no awareness of S3/MinIO — required manually
  writing `profiles.yml` with the `httpfs` extension and explicit `s3_*` settings.
- A working-directory mismatch caused dbt to silently create a second, empty
  `dev.duckdb` file — resolved by understanding dbt-duckdb's relative path resolution.
- A `.gitignore` scoping issue: patterns added to a nested project's `.gitignore`
  don't apply to the parent directory — required adding sensitive folders
  (`secrete`, `.envrc`, `download/`) to the *root* `.gitignore` instead.
- A schema.yml edit that silently failed to save, caught by explicitly re-reading
  the file back before trusting it, rather than assuming the edit worked.

## Open gaps (by design, addressed in later weeks)
- No MDM/match-merge exercise yet (Week 3)
- No AI/RAG or agentic layer yet (Week 4)
- No reporting/analytics layer (Metabase) yet — planned for Week 3 alongside MDM
