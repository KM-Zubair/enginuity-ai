# app/services/chunk.py
from typing import List, Dict
import re

def simple_chunk(text: str, max_chars: int = 1200, overlap: int = 150) -> List[Dict]:
    """Greedy chunker with soft boundaries on paragraph breaks."""
    text = re.sub(r'\n{3,}', '\n\n', text.strip())
    parts: List[str] = []
    i = 0
    while i < len(text):
        j = min(i + max_chars, len(text))
        # try to break on paragraph boundary inside window
        k = text.rfind("\n\n", i, j)
        if k == -1 or j - k < 200:
            k = j
        parts.append(text[i:k].strip())
        i = max(k - overlap, k)  # add overlap only if not at end
    chunks = []
    for idx, p in enumerate([p for p in parts if p]):
        chunks.append({
            "id": f"sec-{idx+1}",
            "title": f"Section {idx+1}",
            "type": "text",
            "content": p
        })
    return chunks
