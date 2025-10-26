"""
ADK Agent definition for ADK Web (no custom UI)

This file exposes a factory function get_agent() that ADK Web can discover.
The agent is named "Ticket_Assignment" and uses DiscoveryEngineSearchTool + BigQueryToolset.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.discovery_engine_search_tool import DiscoveryEngineSearchTool


load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "bom_demo")
BQ_LOCATION = os.getenv("BQ_LOCATION", "us-central1")
RAG_DATA_STORE_ID = os.getenv("RAG_DATA_STORE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


PROMPT = f"""
You are a BOM data analyst answering questions about `{PROJECT_ID}.{DATASET_ID}`.

**MANDATORY PROCESS:**
1. ALWAYS search Discovery Engine FIRST to understand column meanings, terminology mappings, and data types
2. THEN use BigQuery INFORMATION_SCHEMA if you need to verify columns exist
3. THEN build and execute SQL queries
4. Return concise answers with a 'SQL used:' section showing the final query

Tables: item_master, bom_details
"""


def get_agent() -> LlmAgent:
    if not PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is required")

    # BigQuery tool configuration (explicit for readability)
    bq_cfg = BigQueryToolConfig(
        compute_project_id=PROJECT_ID,
        location=BQ_LOCATION,
        max_query_result_rows=100,
    )
    bq_tools = BigQueryToolset(bigquery_tool_config=bq_cfg)

    # Assemble tools list clearly
    tools = [bq_tools]
    if RAG_DATA_STORE_ID:
        rag_tool = DiscoveryEngineSearchTool(
            data_store_id=RAG_DATA_STORE_ID,
            max_results=3,
        )
        tools.append(rag_tool)

    agent = LlmAgent(
        name="bom_data_agent",
        model="gemini-2.5-flash",
        instruction=PROMPT,
        tools=tools,
    )
    return agent


root_agent = get_agent()


