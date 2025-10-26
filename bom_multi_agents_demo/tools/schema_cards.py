"""
Schema Cards Retriever (RAG-lite)
- Loads schema documentation and returns compact "cards" per table/column
"""

import re
from typing import List, Dict


def parse_field_mapping(markdown_text: str) -> List[Dict]:
    """Parse field_mapping_documentation.md into schema cards.

    Very light parser: expects sections per table with bullet lists of columns.
    Returns list of cards: {table, column, type, description}
    """
    cards: List[Dict] = []
    current_table = None

    lines = markdown_text.splitlines()
    for line in lines:
        table_match = re.match(r"^##\s+Table:\s+(.+)$", line.strip())
        if table_match:
            current_table = table_match.group(1).strip()
            continue

        # Expect lines like: - column_name (TYPE): description
        if line.strip().startswith("- ") and current_table:
            m = re.match(r"^-\s+([a-zA-Z0-9_]+)\s+\(([^)]+)\):\s+(.*)$", line.strip())
            if m:
                cards.append({
                    "table": current_table,
                    "column": m.group(1),
                    "type": m.group(2),
                    "description": m.group(3)
                })

    return cards


def retrieve_schema_cards(cards: List[Dict], query: str, top_k: int = 12) -> List[Dict]:
    """Very simple keyword-matching retriever over schema cards.
    In production, replace with Vertex AI Search / vector DB.
    """
    q = query.lower()
    scored: List[Dict] = []
    for c in cards:
        score = 0
        if c["table"].lower() in q:
            score += 2
        if c["column"].lower() in q:
            score += 2
        if any(tok in q for tok in c["description"].lower().split()[:6]):
            score += 1
        if score:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


