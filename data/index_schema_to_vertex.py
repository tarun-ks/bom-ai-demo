"""
One-time indexing script: load schema docs into Vertex AI Search (Discovery Engine)

Prereqs:
  - Enable Discovery Engine API
  - Create a Data Store (Content Search) and note its full resource name
    projects/{PROJECT}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}
  - Set env vars: GCP_PROJECT_ID, RAG_DATA_STORE_ID, BQ_DATASET_ID (optional)

Usage:
  python bom_agentic_demo_with_rag/tools/index_schema_to_vertex.py --file data/field_mapping_documentation.md
  python bom_agentic_demo_with_rag/tools/index_schema_to_vertex.py --file data/field_mapping_documentation.md data/query_patterns_documentation.md
"""

import argparse
import os
import time
import re
from typing import List, Dict, Tuple

from google.cloud import discoveryengine_v1beta as discoveryengine
from google.cloud.discoveryengine_v1beta.types import DataStore as DataStoreType, SolutionType
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import NotFound, AlreadyExists, GoogleAPICallError
from dotenv import load_dotenv


def chunk_markdown(md_text: str) -> List[Dict]:
    """Chunk by table or query ID sections, supporting formats like:
    - ## Table: item_master
    - ## Table 1: item_master
    - ## Query ID: WHERE_USED_001
    """
    chunks: List[Dict] = []
    current_id = None
    current: List[str] = []
    # Match either "Table" or "Query ID" patterns
    pattern = re.compile(r"^##\s*(?:Table(?:\s*\d+)?|Query\s+ID)\s*:?\s*(.+)$", re.IGNORECASE)
    for line in md_text.splitlines():
        m = pattern.match(line.strip())
        if m:
            if current_id and current:
                chunks.append({"id": current_id, "content": "\n".join(current)})
            name = m.group(1).strip()
            safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
            current_id = safe_id
            current = [line]
        else:
            current.append(line)
    if current_id and current:
        chunks.append({"id": current_id, "content": "\n".join(current)})
    return chunks


def _location_from_path(path: str) -> str:
    parts = path.split("/")
    try:
        return parts[3]
    except Exception:
        raise ValueError("Invalid data_store path; expected projects/{project}/locations/{location}/collections/default_collection/dataStores/{id}")


def upsert_documents(data_store: str, chunks: List[Dict]) -> None:
    location = _location_from_path(data_store)
    # Choose correct endpoint
    api_endpoint = "discoveryengine.googleapis.com" if location == "global" else f"{location}-discoveryengine.googleapis.com"
    client = discoveryengine.DocumentServiceClient(client_options=ClientOptions(api_endpoint=api_endpoint))
    for c in chunks:
        doc = discoveryengine.Document(
            id=c["id"],
            content=discoveryengine.Document.Content(
                mime_type="text/plain",
                raw_bytes=c["content"].encode("utf-8"),
            ),
            struct_data={}
        )
        parent = f"{data_store}/branches/default_branch"
        request = discoveryengine.CreateDocumentRequest(
            parent=parent,
            document=doc,
            document_id=c["id"],
        )
        try:
            client.create_document(request=request)
            time.sleep(0.1)
        except Exception:
            # Try update if exists
            # Set full resource name for update
            doc.name = f"{parent}/documents/{c['id']}"
            update_req = discoveryengine.UpdateDocumentRequest(document=doc)
            client.update_document(request=update_req)


def _parse_data_store_path(path: str) -> Tuple[str, str, str]:
    """Parse full data store resource into (project, location, data_store_id)."""
    # Expected: projects/{project}/locations/{location}/collections/default_collection/dataStores/{data_store}
    parts = path.split("/")
    try:
        project = parts[1]
        location = parts[3]
        data_store_id = parts[7]
        return project, location, data_store_id
    except Exception:
        raise ValueError("RAG_DATA_STORE_ID must be a full resource path: projects/{project}/locations/{location}/collections/default_collection/dataStores/{id}")


def ensure_data_store(project: str, location: str, data_store_id: str, display_name: str = None) -> str:
    """Ensure a Discovery Engine Data Store exists; create if missing.

    Returns the full resource name.
    """
    if not display_name:
        display_name = data_store_id

    parent = f"projects/{project}/locations/{location}/collections/default_collection"
    name = f"{parent}/dataStores/{data_store_id}"

    api_endpoint = "discoveryengine.googleapis.com" if location == "global" else f"{location}-discoveryengine.googleapis.com"
    client = discoveryengine.DataStoreServiceClient(client_options=ClientOptions(api_endpoint=api_endpoint))

    # Check existence
    try:
        client.get_data_store(name=name)
        return name
    except NotFound:
        pass

    # Create if not exists (operation) with enum fallbacks for library versions
    try:
        iv_generic = DataStoreType.IndustryVertical.GENERIC  # type: ignore[attr-defined]
    except Exception:
        iv_generic = 1  # GENERIC
    try:
        st_search = SolutionType.SOLUTION_TYPE_SEARCH  # type: ignore[attr-defined]
    except Exception:
        st_search = 1  # SEARCH
    try:
        content_required = DataStoreType.ContentConfig.CONTENT_REQUIRED  # type: ignore[attr-defined]
    except Exception:
        content_required = 2  # CONTENT_REQUIRED

    ds = DataStoreType(
        display_name=display_name,
        industry_vertical=iv_generic,
        solution_types=[st_search],
        content_config=content_required,
    )
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store=ds,
        data_store_id=data_store_id,
    )
    try:
        op = client.create_data_store(request=request)
        result = op.result(timeout=300)
        return result.name
    except AlreadyExists:
        return name
    except GoogleAPICallError as e:
        raise RuntimeError(f"Failed to create data store: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", nargs="+", required=True, help="Path(s) to markdown schema file(s)")
    parser.add_argument("--location", default="global", help="Discovery Engine location (default: global)")
    parser.add_argument("--data_store_id", help="If RAG_DATA_STORE_ID not set, create/use this data store id")
    args = parser.parse_args()

    # Auto-load .env so users don't need to export vars manually
    load_dotenv()

    project = os.getenv("GCP_PROJECT_ID")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID env var is required")
    
    # Expand $GCP_PROJECT_ID placeholder in RAG_DATA_STORE_ID
    data_store = os.getenv("RAG_DATA_STORE_ID")
    if data_store and "$GCP_PROJECT_ID" in data_store:
        data_store = data_store.replace("$GCP_PROJECT_ID", project)

    # Ensure data store exists (from env or args)
    if data_store:
        try:
            # Validate/ensure existing
            proj, loc, ds_id = _parse_data_store_path(data_store)
            # If env path project/location differ from provided flags, prefer path values
            ensured = ensure_data_store(proj, loc, ds_id)
            data_store = ensured
        except Exception as e:
            raise RuntimeError(f"Invalid RAG_DATA_STORE_ID: {e}")
    else:
        if not args.data_store_id:
            raise RuntimeError("RAG_DATA_STORE_ID not set; provide --data_store_id to create one")
        data_store = ensure_data_store(project, args.location, args.data_store_id)

    all_chunks = []
    for file_path in args.file:
        print(f"Processing {file_path}...")
        with open(file_path, "r", encoding="utf-8") as f:
            md = f.read()
        
        chunks = chunk_markdown(md)
        if not chunks:
            print(f"⚠️  No chunks found in {file_path}")
            continue
        
        # Prefix chunk IDs with filename to avoid collisions
        file_prefix = os.path.basename(file_path).replace(".", "_")
        for chunk in chunks:
            chunk["id"] = f"{file_prefix}_{chunk['id']}"
        
        all_chunks.extend(chunks)
        print(f"  → Found {len(chunks)} chunks")
    
    if not all_chunks:
        raise RuntimeError("No chunks parsed from any file. Ensure '## Table:' or '## Query ID:' headers exist.")

    upsert_documents(data_store, all_chunks)
    print(f"✅ Indexed {len(all_chunks)} total chunks into Vertex AI Search")


if __name__ == "__main__":
    main()


