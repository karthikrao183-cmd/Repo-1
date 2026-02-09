from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PyPDF2 import PdfReader


@dataclass(frozen=True)
class Document:
    doc_id: str
    source: str
    text: str
    metadata: dict[str, str]


def _hash_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_local_documents(path: Path) -> list[Document]:
    documents: list[Document] = []
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue
        text = _read_file(file_path)
        if not text.strip():
            continue
        doc_id = _hash_id(str(file_path))
        documents.append(
            Document(
                doc_id=doc_id,
                source=str(file_path),
                text=text,
                metadata={"filename": file_path.name},
            )
        )
    return documents


def _read_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return ""


def chunk_documents(documents: Iterable[Document], chunk_size: int = 800, overlap: int = 120) -> list[Document]:
    chunks: list[Document] = []
    for doc in documents:
        text = doc.text
        start = 0
        index = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk_text = text[start:end]
            chunk_id = _hash_id(f"{doc.doc_id}:{index}")
            chunks.append(
                Document(
                    doc_id=chunk_id,
                    source=doc.source,
                    text=chunk_text,
                    metadata={"parent_id": doc.doc_id, "chunk_index": str(index)},
                )
            )
            start = end - overlap
            if start < 0:
                start = end
            index += 1
    return chunks
