import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Tuple


EXTERNAL_KEYWORDS = (
    "advisor",
    "adviser",
    "consultant",
    "bank",
    "lender",
    "legal",
    "technical",
    "tax",
    "accounting",
    "engineering",
    "market",
    "vdr",
)

MORRISON_KEYWORDS = (
    "morrison",
    "ic paper",
    "phase 1",
    "phase 2",
    "update letter",
    "hum",
)

VERSION_REGEX = re.compile(r"\b(v\d+|version\s*\d+|final)\b", re.IGNORECASE)


@dataclass
class DocumentSelector:
    def select_documents(
        self, documents: List[Dict[str, str]], ic_paper_name: str
    ) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        if not documents:
            raise ValueError("Project Working Folder is empty or missing.")

        ic_paper = next(
            (doc for doc in documents if doc["name"].lower() == ic_paper_name.lower()),
            None,
        )
        if ic_paper is None:
            raise ValueError("IC Paper is required and was not found in Project Working Folder.")

        evidence = [doc for doc in documents if doc["id"] != ic_paper["id"]]
        evidence = self._filter_external(evidence)
        evidence = self._sort_most_recent(evidence)
        return ic_paper, evidence

    def _filter_external(self, documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        external_docs = []
        for doc in documents:
            name_lower = doc["name"].lower()
            if any(keyword in name_lower for keyword in MORRISON_KEYWORDS):
                continue
            if any(keyword in name_lower for keyword in EXTERNAL_KEYWORDS):
                external_docs.append(doc)
        return external_docs

    def _sort_most_recent(self, documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        def version_rank(name: str) -> int:
            match = VERSION_REGEX.search(name)
            if not match:
                return 0
            token = match.group(1).lower()
            if token == "final":
                return 999
            digits = re.findall(r"\d+", token)
            return int(digits[0]) if digits else 0

        def modified_date(value: str) -> datetime:
            if not value:
                return datetime.min
            return datetime.fromisoformat(value.replace("Z", "+00:00"))

        return sorted(
            documents,
            key=lambda doc: (
                version_rank(doc["name"]),
                modified_date(doc.get("last_modified", "")),
            ),
            reverse=True,
        )

    def filter_by_query(self, documents: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
        if not query:
            return documents
        tokens = [token for token in re.split(r"\W+", query.lower()) if token]
        if not tokens:
            return documents
        filtered = [
            doc
            for doc in documents
            if any(token in doc["name"].lower() for token in tokens)
        ]
        return filtered or documents
