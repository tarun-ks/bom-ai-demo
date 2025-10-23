# 🧩 bom-ai-demo

A **GCP-native AI Agent demo** built using the **Google Agent Development Kit (ADK)** that dynamically queries a **BigQuery-based Bill of Materials (BOM)** dataset using natural language.

---

## ☁️ Overview
This demo shows how an LLM agent can interpret manufacturing questions and automatically generate SQL queries to retrieve answers from BigQuery tables.

Example use cases:
- Find serialized or NPI components in a BOM  
- Identify assemblies with obsolete components  
- Fetch Country of Origin (COO) for components  

---

## 🧱 Project Structure


## Project Structure

```
├── data/
│   ├── create_bom_schema.sql
├── app/
│   ├── db_loader.py
│   ├── main.py
│   ├── agent.yaml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Setup

### 1️⃣ Prerequisites
- Python 3.9+
- GCP project with BigQuery API enabled
- Service Account with roles:
  - `BigQuery Data Viewer`
  - `BigQuery Job User`

Authenticate locally:
```bash
gcloud auth application-default login
```

### 2️⃣ Install & Run

```bash
git clone https://github.com/<yourname>/bom-ai-demo.git
cd bom-ai-demo
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env file with your GCP project ID

# Load schema and data
python app/db_loader.py

# Run agent
python app/main.py
```

### 3️⃣ Environment Variables
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Required variables:
- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `BQ_DATASET_ID`: BigQuery dataset name (default: bom_demo)
- `BQ_LOCATION`: BigQuery location (default: us-central1)

## Example Queries

List all serialized components in BOM1001
Show NPI components in Smart Scooter
Find assemblies that have obsolete components
Get COO of components in BOM2001
List BOMs using battery or memory components


