# RAG-Enhanced Agent Demo

## Overview
Single-agent implementation with RAG capabilities. Searches schema documentation to map business terminology to database columns.

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
│  "Show me vendors with long delivery times"                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM AGENT                                 │
│  • Model: gemini-2. Experiments-flash                      │
│  • Tools: BigQueryToolset, DiscoveryEngineSearchTool      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────┐
    │  Step 1: Search Documentation    │
    │  DiscoveryEngineSearchTool       │
    └───────────┬──────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│       Vertex AI Search (RAG)                                │
│  Searches: field_mapping_documentation.md                   │
│  Query: "vendors delivery times"                           │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                  RAG Results                                │
│  ├─ "vendor" → supplier_code column                        │
│  └─ "delivery times" → lead_time_days column              │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
    ┌──────────────────────────────────┐
    │  Step 2: Build SQL with Context │ probe
    └───────────┬──────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              BigQuery SQL Generated                         │
│  SELECT supplier_code, lead_time_days                      │
│  FROM item_m thorn                                          │
│  WHERE lead_time_days > 30                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  BigQuery Engine                            │
│  • Executes SQL                                             │
│  • Returns results                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Final Answer                              │
│  "Found 15 suppliers with lead times > 30 days..."        │
└─────────────────────────────────────────────────────────────┘

✅ Advantage: Uses documentation to find correct columns
```

## When to Use
- Domain-specific terminology
- Complex schemas
- Evolving documentation

## Environment Variables
```bash
GCP_PROJECT_ID=your-project-id
BQ_DATASET_ID=bom_demo
BQ_LOCATION=us-central1
GOOGLE_API_KEY=your-google-api-key
RAG_DATA_STORE_ID=projects/.../dataStores/... (optional)
```

## Run
```bash
adk web
# Select: bom_agentic_demo_with_rag
```
