from dataclasses import dataclass
from typing import List


@dataclass
class ContentChunk:
    doc_name: str
    chunk_id: int
    text: str


def chunk_text(text: str, max_chars: int = 1200) -> List[str]:
    if not text:
        return []
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if current_len + len(paragraph) + 1 > max_chars and current:
            chunks.append("\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += len(paragraph) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def score_chunk(chunk: ContentChunk, query: str) -> int:
    if not query:
        return 0
    tokens = [token for token in query.lower().split() if token]
    if not tokens:
        return 0
    text_lower = chunk.text.lower()
    return sum(text_lower.count(token) for token in tokens)


def search_chunks(chunks: List[ContentChunk], query: str, limit: int = 20) -> List[ContentChunk]:
    if not query:
        return chunks[:limit]
    scored = [(score_chunk(chunk, query), chunk) for chunk in chunks]
    scored.sort(key=lambda item: item[0], reverse=True)
    filtered = [chunk for score, chunk in scored if score > 0]
    return filtered[:limit] if filtered else chunks[:limit]
