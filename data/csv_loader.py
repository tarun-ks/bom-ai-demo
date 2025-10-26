# CSV Data Loader for BigQuery
# This script loads CSV files into BigQuery tables
from google.cloud import bigquery
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "bom_demo")
BQ_LOCATION = os.getenv("BQ_LOCATION", "us-central1")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable is required. Please set it in your .env file.")

print(f"🚀 Initializing BigQuery client for project: {PROJECT_ID}")
client = bigquery.Client(project=PROJECT_ID)

def load_csv_to_bigquery(csv_file_path, table_id, write_disposition="WRITE_TRUNCATE"):
    """
    Load CSV file into BigQuery table
    
    Args:
        csv_file_path (str): Path to CSV file
        table_id (str): BigQuery table ID (format: project.dataset.table)
        write_disposition (str): How to handle existing data
    """
    try:
        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,  # Skip header row
            autodetect=False,  # Use existing table schema
            write_disposition=write_disposition,
            create_disposition=bigquery.CreateDisposition.CREATE_NEVER  # Don't create table, use existing
        )
        
        # Load the CSV file
        with open(csv_file_path, "rb") as source_file:
            job = client.load_table_from_file(
                source_file, 
                table_id, 
                job_config=job_config,
                location=BQ_LOCATION
            )
        
        # Wait for job to complete
        job.result()
        
        # Get table info
        table = client.get_table(table_id)
        print(f"✅ Successfully loaded {table.num_rows} rows into {table_id}")
        
    except Exception as e:
        print(f"❌ Error loading {csv_file_path} into {table_id}: {str(e)}")
        raise

def main():
    """Main function to load all CSV files"""
    
    # Define file mappings
    csv_files = [
        {
            "csv_path": "data/item_master.csv",
            "table_id": f"{PROJECT_ID}.{DATASET_ID}.item_master"
        },
        {
            "csv_path": "data/bom_details.csv", 
            "table_id": f"{PROJECT_ID}.{DATASET_ID}.bom_details"
        }
    ]
    
    print("📦 Starting CSV data load process...")
    
    for file_info in csv_files:
        csv_path = file_info["csv_path"]
        table_id = file_info["table_id"]
        
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV file not found: {csv_path}")
            continue
            
        print(f"📄 Loading {csv_path} into {table_id}...")
        load_csv_to_bigquery(csv_path, table_id)
    
    print("🎉 All CSV files loaded successfully!")
    
    # Display table summary
    print("\n📊 Table Summary:")
    for file_info in csv_files:
        table_id = file_info["table_id"]
        try:
            table = client.get_table(table_id)
            print(f"  {table.table_id}: {table.num_rows} rows, {len(table.schema)} columns")
        except Exception as e:
            print(f"  {table_id}: Error getting table info - {str(e)}")

if __name__ == "__main__":
    main()
