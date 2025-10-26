"""
Agent: ODW_BigQuery_Analyst
Purpose: Natural language → BigQuery SQL generation and execution
Framework: Google ADK Agentic Framework (Sequential + Loop Agents)
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool  # Optional fallback
from google.adk.tools.tool_context import ToolContext

# -------------------------------------------------------------------
# Environment setup
# -------------------------------------------------------------------
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "bom_demo")
BQ_LOCATION = os.getenv("BQ_LOCATION", "us-central1")
RAG_DATA_STORE_ID = os.getenv("RAG_DATA_STORE_ID")

# Force Vertex AI backend: remove API key and set Vertex env vars
if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]

# Set environment variables for ADK to use Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
if PROJECT_ID:
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
if BQ_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = BQ_LOCATION

# -------------------------------------------------------------------
# Global constants
# -------------------------------------------------------------------
PIPELINE_STATE = "pipeline_state"
MAX_RETRIES = 3
MAX_RESULT_ROWS = 100
MAX_BYTES_BILLED = 100_000_000  # 100MB safe limit

# -------------------------------------------------------------------
# Utility to signal loop termination
# -------------------------------------------------------------------
def exit_loop(tool_context: ToolContext):
    tool_context.actions.escalate = True
    return {}

# -------------------------------------------------------------------
# Factory: get_agent()
# -------------------------------------------------------------------
def get_agent() -> SequentialAgent:
    if not PROJECT_ID:
        raise ValueError("Missing env: GCP_PROJECT_ID")

    # ------------------ BigQuery Tool ------------------
    bq_cfg = BigQueryToolConfig(
        compute_project_id=PROJECT_ID,
        location=BQ_LOCATION,
        max_query_result_rows=MAX_RESULT_ROWS,
    )
    bq_tools = BigQueryToolset(bigquery_tool_config=bq_cfg)

    # ------------------ Optional Vertex AI Search Tool ------------------
    rag_tool = None
    if RAG_DATA_STORE_ID:
        # Expand $GCP_PROJECT_ID if present in RAG_DATA_STORE_ID
        datastore_id = RAG_DATA_STORE_ID.replace("$GCP_PROJECT_ID", PROJECT_ID)
        # Only enable if the ID looks valid (contains 'projects/')
        if "projects/" in datastore_id and PROJECT_ID in datastore_id:
            rag_tool = VertexAiSearchTool(
                data_store_id=datastore_id,
                max_results=3,
            )

    # ===================================================================
    # 1. Schema Search Agent (Vertex AI Search ONLY - finds schema/query patterns)
    # ===================================================================
    schema_search_agent = None
    if rag_tool:
        schema_search_agent = LlmAgent(
            name="SchemaSearchAgent",
            model="gemini-2.5-flash",
            instruction=(
                "You search for schema documentation based on the user's question.\n\n"
                "**INPUT:** User's natural language question\n\n"
                "**PROCESS:**\n"
                "1. Extract key terms from user query (e.g., 'suppliers', 'lead time', 'active BOMs')\n"
                "2. Search documentation for:\n"
                "   - Table and column definitions (meanings, data types, relationships)\n"
                "   - Domain terminology mappings (e.g., 'vendor' → supplier_code column)\n"
                "   - Business context (compliance rules, supply chain concepts, etc.)\n\n"
                "**OUTPUT to pipeline_state:**\n"
                "- focus_terms: [list of key search terms extracted]\n"
                "- schema_hints: [list of relevant 'table.column' names found in docs]\n"
                "- domain_terms: {mapping of user terms to database values}\n\n"
                "Example output:\n"
                "{\n"
                "  'focus_terms': ['supplier', 'lead time', 'critical'],\n"
                "  'schema_hints': ['item_master.supplier_code', 'bom_details.lead_time_days'],\n"
                "  'domain_terms': {'critical': 'high priority or long lead time items'}\n"
                "}\n\n"
                "Return updated pipeline_state as JSON."
            ),
            tools=[rag_tool],
            output_key=PIPELINE_STATE,
        )

    # ===================================================================
    # 2. Column Resolver (BigQuery ONLY - verifies and discovers columns)
    # ===================================================================
    column_resolver = LlmAgent(
        name="ColumnResolverAgent",
        model="gemini-2.5-flash",
        instruction=(
            "You identify and verify relevant tables/columns using BigQuery.\n\n"
            f"**INPUT from pipeline_state (provided by SchemaSearchAgent):**\n"
            "- focus_terms: User's key search terms (e.g., ['supplier', 'lead time'])\n"
            "- schema_hints: RAG-suggested columns (e.g., ['item_master.supplier_code', 'bom_details.lead_time_days'])\n"
            "- domain_terms: Terminology mappings (e.g., {{'vendor': 'supplier_code'}})\n\n"
            "**PROCESS:**\n"
            f"1. Query INFORMATION_SCHEMA in `{PROJECT_ID}.{DATASET_ID}` to discover columns in item_master and bom_details\n"
            "2. PRIORITIZE schema_hints columns first (these came from documentation search)\n"
            "3. USE domain_terms to sample DISTINCT values and confirm data matches\n"
            "   Example: If domain_terms mentions 'high priority', check if values like 'CRITICAL' or 'HIGH' exist\n"
            "4. Build candidate_columns list with verified columns\n\n"
            "**OUTPUT to pipeline_state:**\n"
            "- tables: [list of table names to query]\n"
            "- candidate_columns: [verified 'table.column' names]\n"
            "- search_terms: [normalized terms to search for in SQL]\n"
            "- strategy: 1 (always start with exact match strategy)\n\n"
            "Example output:\n"
            "{\n"
            "  'tables': ['item_master', 'bom_details'],\n"
            "  'candidate_columns': ['item_master.supplier_code', 'bom_details.lead_time_days'],\n"
            "  'search_terms': ['SUPPLIER', 'VENDOR'],\n"
            "  'strategy': 1\n"
            "}\n\n"
            "Return updated pipeline_state as JSON."
        ),
        tools=[bq_tools],
        output_key=PIPELINE_STATE,
    )

    # ===================================================================
    # 3. Query Planner (build + refine SQL)
    # ===================================================================
    query_planner = LlmAgent(
        name="QueryPlannerAgent",
        model="gemini-2.5-flash",
        instruction=(
            f"You build safe parameterized BigQuery SQL for `{PROJECT_ID}.{DATASET_ID}`.\n\n"
            "**INPUT from pipeline_state (provided by ColumnResolverAgent):**\n"
            "- tables: Tables to query (e.g., ['item_master', 'bom_details'])\n"
            "- candidate_columns: Verified columns (e.g., ['item_master.supplier_code'])\n"
            "- search_terms: Terms to search for (e.g., ['SUPPLIER', 'VENDOR'])\n"
            "- strategy: Current retry level (1, 2, or 3)\n\n"
            "**PROCESS - Build SQL based on strategy:**\n"
            "Strategy 1: Exact case-insensitive match using LOWER(col) IN UNNEST(@terms_lower)\n"
            "Strategy 2: Regex with plural/singular variants (e.g., 'supplier|suppliers')\n"
            "Strategy 3: Substring contains fallback using LIKE or CONTAINS\n\n"
            "Always:\n"
            "- Project only relevant columns (from candidate_columns)\n"
            "- Add LIMIT 100 for performance\n"
            "- Use parameterized queries for safety\n\n"
            "**OUTPUT to pipeline_state:**\n"
            "- sql: The generated SQL query string\n"
            "- params: Query parameters (if using @param syntax)\n"
            "- attempts_log: Append current attempt info\n\n"
            "Return updated pipeline_state as JSON."
        ),
        output_key=PIPELINE_STATE,
    )

    # ===================================================================
    # 4. Query Executor (loop until results found)
    # ===================================================================
    executor_tools = [bq_tools, exit_loop]
    executor_agent = LlmAgent(
        name="QueryExecutorAgent",
        model="gemini-2.5-flash",
        instruction=(
            "Execute SQL queries using BigQuery and control loop iteration.\n\n"
            "**INPUT from pipeline_state (provided by QueryPlannerAgent):**\n"
            "- sql: The SQL query to execute\n"
            "- params: Query parameters\n"
            "- strategy: Current retry level (1, 2, or 3)\n"
            "- attempts_log: History of previous attempts\n\n"
            "**PROCESS:**\n"
            "1. Execute the SQL query using BigQuery tools\n"
            "2. Check result count:\n"
            "   - If rows > 0: SUCCESS\n"
            "     • Set found_results=true\n"
            "     • Log success details\n"
            "     • CALL exit_loop tool to terminate the loop\n"
            "   - If rows = 0: NO RESULTS\n"
            "     • Set found_results=false\n"
            "     • Increment strategy (1→2→3)\n"
            "     • Continue loop (max 3 iterations)\n\n"
            "**OUTPUT to pipeline_state:**\n"
            "- found_results: boolean\n"
            "- rows: Query results (if found)\n"
            "- chosen_sql: The successful SQL (if found_results=true)\n"
            "- attempts_log: Updated with current attempt\n\n"
            "Return updated pipeline_state as JSON."
        ),
        tools=executor_tools,
        output_key=PIPELINE_STATE,
    )

    refinement_loop = LoopAgent(
        name="RefinementLoop",
        sub_agents=[query_planner, executor_agent],
        max_iterations=MAX_RETRIES,
    )

    # ===================================================================
    # 4. Explainer Agent
    # ===================================================================
    explainer = LlmAgent(
        name="ExplainerAgent",
        model="gemini-2.5-flash",
        instruction=(
            "Summarize query results in natural language for the user.\n\n"
            "**INPUT from pipeline_state (provided by RefinementLoop):**\n"
            "- found_results: boolean indicating success\n"
            "- rows: Query results (if found_results=true)\n"
            "- chosen_sql: The SQL that produced results\n"
            "- attempts_log: History of retry attempts\n\n"
            "**PROCESS:**\n"
            "1. If found_results=true:\n"
            "   - Summarize findings in clear, business-friendly language\n"
            "   - Include key insights from the data\n"
            "2. If found_results=false:\n"
            "   - Explain no results were found after retries\n"
            "   - Suggest alternative search terms or clarifying questions\n"
            "3. Always append a fenced SQL code block showing the executed query\n\n"
            "**OUTPUT:**\n"
            "Natural language summary + SQL block\n\n"
            "Example:\n"
            "Found 15 suppliers with lead times over 30 days:\n"
            "- ACME Corp: 45 days average\n"
            "- TechParts Inc: 38 days average\n"
            "...\n\n"
            "SQL used:\n"
            "```sql\n"
            "SELECT supplier_code, AVG(lead_time_days) as avg_lead_time\n"
            "FROM item_master\n"
            "WHERE lead_time_days > 30\n"
            "GROUP BY supplier_code\n"
            "LIMIT 100\n"
            "```"
        ),
        output_key="final_answer",
    )

    # ===================================================================
    # Root Sequential Flow
    # ===================================================================
    # State flows through pipeline_state key in session:
    # 1. SchemaSearchAgent      → pipeline_state: {focus_terms, schema_hints, domain_terms}
    # 2. ColumnResolverAgent    → pipeline_state: {...previous, tables, candidate_columns, search_terms, strategy}
    # 3. RefinementLoop         → pipeline_state: {...previous, sql, params, found_results, rows, chosen_sql}
    #    ├─ QueryPlannerAgent   → builds SQL based on strategy
    #    └─ QueryExecutorAgent  → executes SQL, calls exit_loop on success
    # 4. ExplainerAgent         → final_answer: natural language + SQL block
    
    sub_agents_list = []
    if schema_search_agent:
        sub_agents_list.append(schema_search_agent)
    sub_agents_list.extend([column_resolver, refinement_loop, explainer])

    root = SequentialAgent(
        name="ODW_BigQuery_Analyst",
        sub_agents=sub_agents_list,
    )

    return root


root_agent = get_agent()
