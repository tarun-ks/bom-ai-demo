# Simple Agent Demo

## Overview
Basic single-agent implementation that generates BigQuery SQL directly from user queries.

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
│  "Show me products with serialized components"             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM AGENT                                 │
│  • Model: gemini-2.5-flash                                 │
│  • Tools: BigQueryToolset                                  │
│  • Direct SQL generation                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              BigQuery SQL Generated                         │
│  SELECT * FROM item_master                                  │
│  WHERE is_serialized = TRUE                                 │
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
│  "Found 25 serialized components in the database..."       │
└─────────────────────────────────────────────────────────────┘

⚠️ Limitation: LLM must guess column names from context only
```

## When to Use
- Quick prototyping
- Straightforward queries where column names are obvious
- Simple use cases

## Environment Variables
```bash
GCP_PROJECT_ID=your-project-id
BQ_DATASET_ID=bom_demo
BQ_LOCATION=us-central1
```

## Run
```bash
adk web
# Select: bom_simple_agentic_demo
```
