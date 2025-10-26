# Database loader module
# This file will contain database loading functionality
from google.cloud import bigquery
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your GCP project
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "bom_demo")
BQ_LOCATION = os.getenv("BQ_LOCATION", "us-central1")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable is required. Please set it in your .env file.")

print(f"🚀 Initializing BigQuery client for project: {PROJECT_ID}")
client = bigquery.Client(project=PROJECT_ID, location=BQ_LOCATION)

# Execute the SQL file
with open("data/create_bom_schema.sql", "r") as f:
    query = f.read().replace("<YOUR_PROJECT_ID>", PROJECT_ID)

print("📦 Executing SQL script to create tables and load sample data...")
job = client.query(query)
job.result()

print("✅ BigQuery tables created successfully under dataset:", DATASET_ID)
