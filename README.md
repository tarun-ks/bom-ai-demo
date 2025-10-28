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

**Option A: Run Locally**

```bash
git clone https://github.com/<yourname>/bom-ai-demo.git
cd bom-ai-demo
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env file with your GCP project ID and GOOGLE_API_KEY

# Load schema and data
python data/db_loader.py
python data/csv_loader.py

# Optional: Setup RAG (for RAG-enhanced agents)
gcloud services enable discoveryengine.googleapis.com --project=<your-project>
python data/index_schema_to_vertex.py \
  --file data/field_mapping_documentation.md \
  --data_store_id bom-schema-store \
  --location global

# Run ADK Web (opens UI at http://localhost:8000)
adk web
```

**Option B: Run in Cloud Shell**

```bash
# Start Cloud Shell in Google Cloud Console
git clone https://github.com/tarun-ks/bom-ai-demo.git
cd bom-ai-demo

# Setup environment
python3 -m venv venv && source venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# Configure .env
cp .env.example .env
PROJECT_ID=$(gcloud config get-value project)
sed -i "s/^GCP_PROJECT_ID=.*/GCP_PROJECT_ID=$PROJECT_ID/" .env

# Add GOOGLE_API_KEY to .env (get from Google AI Studio)
echo "GOOGLE_API_KEY=your-api-key-here" >> .env

# Load schema and data
python data/db_loader.py
python data/csv_loader.py

# Optional: Setup RAG (for RAG-enhanced agents)
gcloud services enable discoveryengine.googleapis.com --project=$PROJECT_ID
python data/index_schema_to_vertex.py \
  --file data/field_mapping_documentation.md \
  --data_store_id bom-schema-store \
  --location global

# Run ADK Web
adk web
# Use Cloud Shell Web Preview (port 8080)
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
- `GOOGLE_API_KEY`: Google AI API key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))
- `RAG_DATA_STORE_ID`: Vertex AI Search data store ID (auto-generated during RAG setup)

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
- List all serialized components in BOM039
- Show NPI components in Smart Scooter
- Find assemblies that have obsolete components
- Get COO of components in BOM001
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

## 🔑 Getting Your Google AI API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add it to your `.env` file as `GOOGLE_API_KEY=your-key-here`
---
