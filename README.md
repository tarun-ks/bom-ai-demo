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

```
├── data/
│   ├── create_bom_schema.sql           # BigQuery schema definition
│   ├── db_loader.py                    # Schema creation script
│   ├── csv_loader.py                   # Data loading script
│   ├── item_master.csv                 # Sample item master data (500+ rows)
│   ├── bom_details.csv                 # Sample BOM details data (500+ rows)
│   ├── field_mapping_documentation.md  # Schema documentation for RAG
│   ├── query_patterns_documentation.md # Query templates for reuse
│   └── index_schema_to_vertex.py       # Script to index docs into Vertex AI Search
├── bom_simple_agentic_demo/
│   └── agent.py                        # Demo 1: Basic single agent
├── bom_agentic_demo_with_rag/
│   └── agent.py                        # Demo 2: Single agent with RAG
├── bom_multi_agents_demo/
│   └── agent.py                        # Demo 3: Multi-agent pipeline
├── requirements.txt
├── README.md
├── .env.example                        # Environment template
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
python data/db_loader.py

# Load CSV data into BigQuery
python data/csv_loader.py

# Run ADK Web (opens UI at http://localhost:8000)
adk web
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
- `GOOGLE_API_KEY`: Google AI API key (for simple/RAG demos)
- `RAG_DATA_STORE_ID`: Vertex AI Search data store ID (for RAG demos)

---

## 🎯 Demo Approaches

This project includes **three progressive implementations** to showcase different levels of sophistication:

### 1. **Basic Agent** (`bom_simple_agentic_demo/`)
- Single LLM agent with direct BigQuery access
- Fast and simple
- Best for: Quick prototyping, straightforward queries
- **Run:** Select `bom_simple_agentic_demo` in ADK Web

### 2. **RAG-Enhanced Agent** (`bom_agentic_demo_with_rag/`)
- Single agent + Vertex AI Search for schema documentation
- Understands business terminology via RAG
- Best for: Domain-specific language, evolving schemas
- **Run:** Select `bom_agentic_demo_with_rag` in ADK Web

### 3. **Multi-Agent Pipeline** (`bom_multi_agents_demo/`)
- Sequential multi-agent workflow with retry logic
- Self-healing queries (case, plurals, typos)
- Production-grade error handling
- Best for: Enterprise deployment, complex analytics
- **Run:** Select `bom_multi_agents_demo` in ADK Web


---

## Example Queries

### Basic BOM Analysis
- List all serialized components in BOM1001
- Show NPI components in Smart Scooter
- Find assemblies that have obsolete components
- Get COO of components in BOM2001
- List BOMs using battery or memory components

### Advanced Manufacturing Analytics
- What's the total cost breakdown by supplier for all electric bikes?
- Which components have the highest scrap factors and why?
- Show me all NPI components with their compliance status and lead times
- What's the labor hour distribution across different product categories?
- Which products use carbon fiber components and what's the cost impact?

### Supply Chain & Sourcing
- Find all components from German suppliers with their quality requirements
- What's the weight distribution of components in the cargo scooter vs mountain bike?
- Which obsolete components are still referenced in active BOMs?
- What's the total battery capacity across all products?
- Show me the cost impact of using titanium vs aluminum components

### Production & Quality
- What's the total setup time for manufacturing the Electric Mountain Bike?
- Which components require special tooling and what are the requirements?
- Show me all components with yield factors below 98%
- What are the quality requirements for all serialized components?
- Which BOMs have the highest total labor hours?

### Cost & Performance Analysis
- What's the most expensive component in each product category?
- Which suppliers have the longest lead times for critical components?
- Show me the cost per unit weight for all frame components
- What's the total cost of all NPI components across all products?
- Which products have the highest total component cost?


---

## 🚀 Run in Cloud Shell (no local setup)

You can run the full demo directly in Google Cloud Shell.

### 1) Start Cloud Shell
- Open Google Cloud Console → Cloud Shell (top-right terminal icon)
- Clone and enter the repo:
```bash
git clone https://github.com/tarun-ks/bom-ai-demo.git
cd bom-ai-demo
```

### 2) Configure environment
```bash
python3 -m venv venv && source venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# Create .env (or export directly in the shell)
cp .env.example .env
sed -i "" "s/^GCP_PROJECT_ID=.*/GCP_PROJECT_ID=$(gcloud config get-value project)/" .env || true

# Authenticate (ADC used by BigQuery/RAG tools)
gcloud auth application-default login
```

### 3) Load sample schema and data (optional)
```bash
python data/db_loader.py
python data/csv_loader.py
```

### 4) Launch ADK Web
```bash
adk web --host 0.0.0.0 --port 8080
```
Cloud Shell will show a Web Preview link (port 8080). Open it and select one of the agents.

---

## 📚 Index schema docs into Vertex AI Search (RAG)

Index `data/field_mapping_documentation.md` (and optionally `data/query_patterns_documentation.md`) into Vertex AI Search using the script.

### Prereqs
- Enable Discovery Engine API
- Either set a full `RAG_DATA_STORE_ID` or pass `--data_store_id`

`RAG_DATA_STORE_ID` format:
```
projects/$GCP_PROJECT_ID/locations/global/collections/default_collection/dataStores/bom-schema-store
```

### Run the script
```bash
export GCP_PROJECT_ID=<your-project>

# Option A: Use existing RAG_DATA_STORE_ID from .env
python data/index_schema_to_vertex.py \
  --file data/field_mapping_documentation.md

# Option B: Create/ensure a data store and index
python data/index_schema_to_vertex.py \
  --file data/field_mapping_documentation.md \
  --data_store_id bom-schema-store \
  --location global

# Multiple files
python data/index_schema_to_vertex.py \
  --file data/field_mapping_documentation.md data/query_patterns_documentation.md \
  --data_store_id bom-schema-store --location global
```

The script validates/creates the data store, chunks markdown by headers, and upserts chunks into Vertex AI Search for RAG.
