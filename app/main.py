# Main application entry point
# This file will contain the main application logic
from google.adk import Agent
from google.adk.tools.bigquery_tool import BigQueryTool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "bom_demo")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable is required. Please set it in your .env file.")

print("🤖 Starting bom-ai-demo agent with BigQuery backend...")

# Initialize Agent
agent = Agent.from_yaml(
    "app/agent.yaml",
    tools=[
        BigQueryTool(
            project_id=PROJECT_ID,
            description=f"Query access for dataset {DATASET_ID}"
        )
    ]
)

print("✅ Agent is ready! Ask your questions (type 'exit' to quit)\n")

while True:
    question = input("💬 You: ")
    if question.lower() in ["exit", "quit"]:
        break
    print("🔍 Agent:", agent.chat(question))
