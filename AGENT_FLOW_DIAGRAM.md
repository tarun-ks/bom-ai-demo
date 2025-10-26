# BOM Agentic System - Agent Flow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER QUESTION                                   │
│              "List BOMs using battery or memory components"              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ROOT AGENT: SequentialAgent                           │
│                     (Orchestrates 4 sub-agents in order)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │    Sequential Execution       │
                    └───────────────┬───────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌─────────────────┐      ┌─────────────┐      ┌───────────────┐
    │    Agent 1      │ ───▶ │   Agent 2   │ ───▶ │   Agent 3     │
    │  SchemaSearch   │      │   Column    │      │ RefinementLoop│
    │   (RAG-only)    │      │  Resolver   │      │  (LoopAgent)  │
    │   (Optional)    │      │             │      │               │
    └─────────────────┘      └─────────────┘      └───────────────┘
                                                            │
                                                            ▼
                                                    ┌───────────────┐
                                                    │   Agent 4     │
                                                    │   Explainer   │
                                                    └───────────────┘
                                                            │
                                                            ▼
                                                    ┌───────────────┐
                                                    │ FINAL ANSWER  │
                                                    │  + SQL Used   │
                                                    └───────────────┘
```

---

## Detailed Agent Flow

### 🔍 Agent 1: SchemaSearchAgent (LlmAgent) [OPTIONAL - only if RAG enabled]

**Purpose**: Search Vertex AI Search for schema documentation and domain terminology

**Input**: User question (extracts focus terms directly from the question)

**Process**:
```
User Question: "List BOMs using battery or memory components"
     │
     ▼
Extract focus_terms: ["battery", "memory", "BOMs"]
     │
     ▼
┌──────────────────────────────────┐
│ Vertex AI Search Tool            │
│ Query: "battery memory columns"  │
└──────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Retrieve from indexed docs:      │
│ - field_mapping_documentation.md │
│ - query_patterns_documentation   │
└──────────────────────────────────┘
     │
     ▼
Parse results:
- Table definitions
- Column meanings (category = tech domain)
- Domain terms (ELECTRONICS, BATTERY)
```

**Output** → `pipeline_state`:
```json
{
  "focus_terms": ["battery", "memory", "BOM"],
  "schema_hints": ["item_master.category", "item_master.item_description"],
  "domain_terms": {
    "battery": "ELECTRONICS category",
    "memory": "ELECTRONICS category"
  }
}
```

**Tools**: `VertexAiSearchTool` (retrieval/search only)

---

### 📊 Agent 2: ColumnResolverAgent (LlmAgent)

**Purpose**: Verify columns exist in BigQuery and sample values

**Input**: `pipeline_state.schema_hints`, `pipeline_state.focus_terms`

**Process**:
```
schema_hints: ["item_master.category"]
     │
     ▼
┌────────────────────────────────────┐
│ BigQuery Tool                      │
│ Query INFORMATION_SCHEMA           │
│ for STRING columns                 │
└────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Sample DISTINCT values:            │
│ SELECT DISTINCT category           │
│ FROM item_master LIMIT 10          │
└────────────────────────────────────┘
     │
     ▼
Confirm: "BATTERY", "MEMORY" exist
Build candidate_columns list
```

**Output** → `pipeline_state` (updated):
```json
{
  "intent": "lookup",
  "focus_terms": ["battery", "memory"],
  "schema_hints": ["item_master.category"],
  "domain_terms": {...},
  "tables": ["item_master", "bom_details"],
  "candidate_columns": ["item_master.category", "bom_details.component_item_number"],
  "search_terms": ["battery", "memory"],
  "strategy": 1
}
```

**Tools**: `BigQueryToolset` (function-calling only)

---

### 🔄 Agent 3: RefinementLoop (LoopAgent with 2 sub-agents)

**Purpose**: Build SQL, execute with retries, exit on success

**Max Iterations**: 3

#### Sub-Agent 4a: QueryPlannerAgent (LlmAgent)

**Purpose**: Build parameterized SQL based on current strategy

**Input**: `pipeline_state.strategy`, `pipeline_state.candidate_columns`, `pipeline_state.search_terms`

**Process**:
```
Strategy 1: Exact case-insensitive
     │
     ▼
┌──────────────────────────────────────────────────┐
│ Build SQL:                                       │
│ SELECT DISTINCT bd.parent_item_number, ...      │
│ FROM bom_details bd                              │
│ JOIN item_master im                              │
│   ON bd.component_item_number = im.item_number  │
│ WHERE LOWER(im.category) IN                     │
│   UNNEST(@terms_lower)                          │
│   AND bd.is_active = TRUE                       │
│ LIMIT 100                                       │
└──────────────────────────────────────────────────┘
     │
     ▼
Set params: {"terms_lower": ["battery", "memory"]}
```

**Output** → `pipeline_state` (updated):
```json
{
  ...(previous fields),
  "sql": "SELECT DISTINCT bd.parent_item_number...",
  "params": {"terms_lower": ["battery", "memory"]},
  "attempts_log": ["Strategy 1: exact match"]
}
```

**Tools**: None (SQL generation only)

---

#### Sub-Agent 4b: QueryExecutorAgent (LlmAgent)

**Purpose**: Execute SQL, check results, decide to continue or exit loop

**Input**: `pipeline_state.sql`, `pipeline_state.params`

**Process**:
```
Execute SQL via BigQuery
     │
     ├─── rows > 0? ────┐
     │                  │
     YES                NO
     │                  │
     ▼                  ▼
found_results=true    found_results=false
     │                  │
     ▼                  ▼
CALL exit_loop()    strategy++
     │                  │
     ▼                  ▼
Loop STOPS          Retry with Strategy 2
                    (plural/singular regex)
                         │
                         └─── If still no results ───┐
                                                      │
                                                      ▼
                                              Strategy 3
                                          (substring contains)
                                                      │
                                                      └─── If still no results
                                                           after 3 iterations
                                                           → STOP (max reached)
```

**Decision Tree**:
```
Iteration 1 (Strategy 1):
   └─ SQL: LOWER(category) IN UNNEST(@terms_lower)
   └─ Result: 0 rows → Continue to iteration 2

Iteration 2 (Strategy 2):
   └─ SQL: REGEXP_CONTAINS(category, r'(?i)\b(battery|batteries|memory|memories)\b')
   └─ Result: 5 rows → FOUND! → exit_loop() → STOP

(Iteration 3 would be substring fallback, not reached in this case)
```

**Output** → `pipeline_state` (final):
```json
{
  ...(all previous fields),
  "found_results": true,
  "chosen_sql": "SELECT DISTINCT bd.parent_item_number...",
  "attempts_log": [
    "Strategy 1: exact match - 0 rows",
    "Strategy 2: regex variants - 5 rows (SUCCESS)"
  ],
  "rows": [...query results...],
  "strategy": 2
}
```

**Tools**: 
- `BigQueryToolset` (execute SQL)
- `exit_loop` (signal loop termination)

---

### 📝 Agent 4: ExplainerAgent (LlmAgent)

**Purpose**: Summarize results in natural language and show SQL used

**Input**: `pipeline_state` (complete with results and SQL)

**Process**:
```
Read pipeline_state.rows
Read pipeline_state.chosen_sql
     │
     ▼
┌────────────────────────────────────┐
│ Generate natural language summary: │
│ "Found 5 BOMs using battery or    │
│  memory components: EB-001, ..."   │
└────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Append SQL block:                  │
│ ```sql                            │
│ SELECT DISTINCT bd.parent_item... │
│ ```                               │
└────────────────────────────────────┘
```

**Output** → `final_answer`:
```
Found 5 BOMs using battery or memory components:
- EB-001: Electronic Board Assembly
- EB-002: Advanced Circuit Module
- ...

SQL used:
```sql
SELECT DISTINCT bd.parent_item_number, im.item_description
FROM `mvp-project-474715.bom_demo.bom_details` bd
JOIN `mvp-project-474715.bom_demo.item_master` im 
  ON bd.component_item_number = im.item_number
WHERE REGEXP_CONTAINS(im.category, r'(?i)\b(battery|batteries|memory|memories)\b')
  AND bd.is_active = TRUE
LIMIT 100
```
```

**Tools**: None (LLM reasoning only)

---

## State Flow Visualization

```
pipeline_state evolution:

┌─────────────────────────────────────────────────────────────────┐
│ After SchemaSearch (optional):                                  │
│ { focus_terms, schema_hints, domain_terms }                    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ After ColumnResolver:                                           │
│ { ..., tables, candidate_columns, search_terms, strategy: 1 }  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Loop Start   │
                    └───────────────┘
                            │
            ┌───────────────┼───────────────┐
            │                               │
            ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ QueryPlanner adds:      │    │ Executor checks:        │
│ { sql, params,          │───▶│ { found_results,        │
│   attempts_log }        │    │   rows, chosen_sql }    │
└─────────────────────────┘    └─────────────────────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                                     │
                  found_results?                              │
                        │                                     │
                  ┌─────┴─────┐                              │
                  │           │                              │
                 YES          NO                             │
                  │           │                              │
                  │      strategy++                          │
                  │      loop again                          │
                  │           │                              │
                  │           └──────────────────────────────┘
                  │
              exit_loop()
                  │
                  ▼
        ┌───────────────┐
        │  Loop End     │
        └───────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ After Explainer:                                                │
│ final_answer: "Natural language summary + SQL block"           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tool Usage by Agent

| Agent | Tools | Tool Type | Purpose |
|-------|-------|-----------|---------|
| SchemaSearch | VertexAiSearchTool | Retrieval/Search | Query RAG docs |
| ColumnResolver | BigQueryToolset | Function-calling | INFORMATION_SCHEMA + sampling |
| QueryPlanner | None | - | SQL generation |
| QueryExecutor | BigQueryToolset + exit_loop | Function-calling | Execute SQL + control loop |
| Explainer | None | - | Natural language generation |

---

## Key Design Patterns

### 1. Sequential Orchestration
```
SequentialAgent ensures ordered execution:
  Agent 1 → Agent 2 → Agent 3 → Agent 4
  (SchemaSearch → ColumnResolver → RefinementLoop → Explainer)
```

### 2. Loop Agent Pattern
```
LoopAgent provides deterministic retries:
  - Max 3 iterations
  - Incrementing strategy (exact → regex → substring)
  - exit_loop() tool for early termination
```

### 3. Tool Separation (No Mixing)
```
SchemaSearch:    VertexAiSearchTool ONLY
ColumnResolver:  BigQueryToolset ONLY
QueryExecutor:   BigQueryToolset ONLY

→ Avoids Gemini "Multiple tools" API constraint
```

### 4. State-Based Communication
```
All agents read/write pipeline_state
→ Shared context across entire flow
→ Observable in debug traces
```

### 5. Self-Healing Queries
```
Strategy escalation ladder:
  1. Exact case-insensitive
  2. Plural/singular regex
  3. Substring contains
→ Handles typos, case issues, synonyms
```

---

## Error Handling Flow

```
                    User Question
                         │
                         ▼
              ┌──────────────────┐
              │ SchemaSearch     │
              └──────────────────┘
                         │
                 ┌───────┴───────┐
                 │ RAG empty?    │
                 └───────┬───────┘
                    NO   │   YES
                         │    │
                         │    └──▶ Skip, continue with defaults
                         │
                         ▼
              ┌──────────────────┐
              │ ColumnResolver   │
              └──────────────────┘
                         │
                 ┌───────┴───────┐
                 │ Columns       │
                 │ found?        │
                 └───────┬───────┘
                    YES  │   NO
                         │    │
                         │    └──▶ Return "No matching columns"
                         │
                         ▼
              ┌──────────────────┐
              │ RefinementLoop   │
              └──────────────────┘
                         │
                 ┌───────┴───────┐
                 │ Results       │
                 │ found?        │
                 └───────┬───────┘
                    YES  │   NO (after 3 tries)
                         │    │
                         │    └──▶ Return "No results found"
                         │         + suggest top values
                         │
                         ▼
                   SUCCESS
```

---

## Performance Characteristics

| Stage | Avg Time | Tokens | Cost (approx) |
|-------|----------|--------|---------------|
| SchemaSearch | 1-2s | ~800 | $0.0002 |
| ColumnResolver | 2-3s | ~1000 | $0.0003 |
| RefinementLoop (1 iter) | 3-5s | ~1500 | $0.0004 |
| Explainer | 1-2s | ~600 | $0.0001 |
| **TOTAL** | **7-12s** | **~3900** | **$0.0010** |

*Notes:*
- Times assume network latency ~200ms
- Loop iterations add 3-5s each
- RAG lookup adds ~500ms
- BigQuery queries typically <1s

---

## Future Enhancements (Query Reuse Pattern)

When query_patterns_documentation.md is enabled:

```
┌─────────────────────────────────────────────────────────────────┐
│ SchemaSearchAgent (Enhanced)                                    │
│                                                                 │
│ Search Vertex AI Search                                        │
│     │                                                           │
│     ├─ Find Query ID? (similarity > 0.85)                      │
│     │    YES → Set reuse_query=true, sql_template=...         │
│     │    NO  → Set reuse_query=false, use schema_hints        │
│     │                                                           │
│     └─▶ Add to pipeline_state                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ QueryPlannerAgent (Enhanced)                                    │
│                                                                 │
│ Check pipeline_state.reuse_query:                              │
│     │                                                           │
│     ├─ TRUE  → Adapt sql_template (parameter substitution)    │
│     └─ FALSE → Build new SQL (existing retry strategy)        │
└─────────────────────────────────────────────────────────────────┘

Benefits:
- 5-10x faster (skip SQL generation)
- Higher quality (validated queries)
- Consistent results
```

---

## Summary

**Agent Count**: 4 (3 LlmAgents + 1 LoopAgent with 2 sub-agents)

**Tool Count**: 3 unique tools
- VertexAiSearchTool (RAG retrieval)
- BigQueryToolset (schema + data queries)
- exit_loop (loop control)

**State Keys**: Single `pipeline_state` object with cumulative fields

**Retry Strategy**: 3-level ladder (exact → regex → substring)

**Observability**: All steps logged in `attempts_log`

**Error Handling**: Graceful degradation at each stage

