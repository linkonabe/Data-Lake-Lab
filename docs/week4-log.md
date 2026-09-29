# Week 4 — RAG & AI-Ready Data Layer: Outcome & Skills Log

## What was built
- Qdrant vector database added to the local stack via Docker Compose — a second
  storage type alongside MinIO (object) and DuckDB (relational), each serving a
  distinct purpose in the lakehouse.
- All 1,387 active companies embedded (sentence-transformers, all-MiniLM-L6-v2) as
  natural-language documents and upserted into Qdrant for semantic search.
- A postcode-to-region enrichment step, added after retrieval testing exposed a real
  gap: raw postcodes carry no learnable geographic meaning to a general-purpose
  embedding model. Enrichment measurably improved named-region queries (e.g.
  "Scotland") while a documented, understood limitation remains on relative/
  directional queries (e.g. "north of England") — a known trade-off of small
  embedding models with non-named-entity geography, not something engineered around
  given project timeline.
- A grounded generation layer using a locally-run LLM (Ollama, llama3.2:3b) — zero
  cloud cost, zero data leaving the environment. Two independent grounding
  mechanisms: a numeric relevance-score gate before generation is attempted at all,
  and an explicit "answer only from context, say so if you can't" prompt instruction.

## Evaluation findings (tested deliberately, not assumed)
- Out-of-domain query ("breweries in Nigeria") correctly refused — proved the
  prompt-level grounding instruction functions independently of the relevance-score
  gate, since the retrieved score was above threshold but the model still declined.
- A groundedness check on retrieved context vs. generated citations found the model
  did NOT hallucinate company names, but DID silently omit a more relevant result
  (a company with "Yorkshire" literally in its name, ranked above one it did
  include) — a distinct failure mode from hallucination: incomplete use of
  provided context rather than fabrication. Documented as an honest limitation of
  small local models rather than hidden or "fixed" superficially.

## Skills acquired, mapped to Lead AI & Data Engineer job requirements

| Job posting language | What I can now demonstrate |
|---|---|
| "AI-ready data foundations... RAG, conversational AI" | Full RAG pipeline: embedding, vector storage, retrieval, grounded generation, built and evaluated end to end |
| "responsible AI standards" | Two independent grounding mechanisms designed specifically to prevent hallucination on out-of-domain queries, tested and confirmed working |
| "engineering discipline... translate business problems" | Diagnosed a real geographic-retrieval gap, root-caused it correctly, applied a targeted fix, and knew when further engineering wasn't worth the time given project constraints |

## Open gaps (acknowledged, not pursued given timeline)
- No agentic/multi-step tool-calling layer or MCP server built — scoped as a stretch
  goal from the outset given a 3-4 week window; the RAG foundation this would sit on
  top of is complete and working.
- No reporting/dashboard layer (Metabase) — deliberately deprioritized in favor of
  the AI-readiness layer, which the job posting weighted equally to reporting.
