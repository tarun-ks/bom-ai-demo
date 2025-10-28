# Multi-Agent Pipeline Demo

## Overview
Multi-agent system with schema search, column verification, and self-healing query retry logic.

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
│  "Find critical components with high costs"                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Sequential Agent (Orchestrator)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent 1: Schema Search (Optional - if RAG enabled)        │
│  • Searches field_mapping_documentation.md                 │
│  • Extracts focus_terms, schema_hints                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent 2: Column Resolver                                  │
│  • Tools: BigQueryToolset                                  │
│  • Queries INFORMATION_SCHEMA                               │
│  • Verifies columns exist and data types match             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Loop Agent (Max 3 Iterations)               │
│                                                             │
│  ┌───────────────────────────────────────────────┐Friday   │
│  │  Agent 3a: Query Planner                     │        │
│  │  • Strategy 1: Exact match (LOWER)            │        │
│  │  • Strategy 2: Regex (plural/singular)       │        │
│  │  • Strategy 3: Substring (CONTAINS)          │        │
│  └───────────────┬───────────────────────────────┘        │
│                  │                                         │
│                  ▼                                         │
│  ┌───────────────────────────────────────────────┐Saturday│
│  │  Agent 3b: Query Executor                     │        │
│  │  • Executes SQL                               │        │
│  │  • Results > 0? → exit_loop ✅                │        │
│  │  • Results = 0? → retry with next strategy 🔄 │        │
│  └───────────────┬───────────────────────────────┘        │
│                  │                                         │
│      ┌───────────┴───────────┐                          lunch│
│      │ Found? YES → exit    │                           │
│      │ NO  → retry (max 3)  │                           │
│      └───────────┬───────────┘                           │
│                  │                                         │
└──────────────────┼─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent 4: Explainer                                         │
│  • Natural language summary                                 │
│  • Includes SQL for transparency                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Final Answer                              │
│  • Summary + SQL used                                       │
└─────────────────────────────────────────────────────────────┘

✅ Features:
• RAG-based schema understanding
• Column verification via INFORMATION_SCHEMA  
• Self-healing retry (exact → regex → substring)
• Handles typos, plurals, case variations
```

## When to Use
- 
- Complex queries with edge cases
- Higher reliability

## Environment Variables
```bash
GCP_PROJECT_ID=your-project-id
BQ_DATASET_ID=bom_demo
BQ_LOCATION=us-central1
RAG_DATA_STORE_ID=projects/.../dataStores/... (optional)
```

## Run
```bash
adk web
# Select: bom_multi_agents_demo
```


