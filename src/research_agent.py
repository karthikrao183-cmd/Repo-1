from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from .config import AzureOpenAIConfig
from .document_loader import Document


@dataclass
class Evidence:
    chunk: Document
    score: float


class RecursiveResearchAgent:
    def __init__(
        self,
        *,
        openai_config: AzureOpenAIConfig,
        max_depth: int = 3,
        max_evidence: int = 6,
    ) -> None:
        self.openai_config = openai_config
        self.max_depth = max_depth
        self.max_evidence = max_evidence
        credential = (
            AzureKeyCredential(openai_config.api_key)
            if openai_config.api_key
            else DefaultAzureCredential(exclude_interactive_browser_credential=True)
        )
        self.client = ChatCompletionsClient(
            endpoint=openai_config.endpoint,
            credential=credential,
            api_version=openai_config.api_version,
        )

    def _embedding_client(self):
        from azure.ai.inference import EmbeddingsClient
        credential = (
            AzureKeyCredential(self.openai_config.api_key)
            if self.openai_config.api_key
            else DefaultAzureCredential(exclude_interactive_browser_credential=True)
        )

        return EmbeddingsClient(
            endpoint=self.openai_config.endpoint,
            credential=credential,
            api_version=self.openai_config.api_version,
        )

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        embeddings_client = self._embedding_client()
        response = embeddings_client.embed(
            model=self.openai_config.embedding_deployment,
            input=texts,
        )
        return np.array([item.embedding for item in response.data])

    def _score_chunks(self, query: str, chunks: list[Document]) -> list[Evidence]:
        if not chunks:
            return []
        embeddings = self._embed_texts([query] + [chunk.text for chunk in chunks])
        query_vec = embeddings[0]
        chunk_vecs = embeddings[1:]
        norm_query = query_vec / np.linalg.norm(query_vec)
        norm_chunks = chunk_vecs / np.linalg.norm(chunk_vecs, axis=1, keepdims=True)
        scores = norm_chunks @ norm_query
        evidence = [Evidence(chunk=chunk, score=float(score)) for chunk, score in zip(chunks, scores)]
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[: self.max_evidence]

    def _ask_llm(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt),
            ],
            model=self.openai_config.deployment,
            temperature=0.2,
        )
        return response.choices[0].message.content

    def _plan_followups(self, query: str, evidence: list[Evidence]) -> list[str]:
        citations = "\n".join(
            f"- {item.chunk.source}: {item.chunk.text[:200]}" for item in evidence
        )
        prompt = (
            "You are a research planner. Based on the query and evidence, list up to 3 "
            "follow-up questions that would improve the answer. Reply as bullet points."
        )
        response = self._ask_llm(
            "Return concise follow-up questions.",
            f"Query: {query}\nEvidence:\n{citations}\n",
        )
        followups = [line.strip("- ") for line in response.splitlines() if line.strip()]
        return followups[:3]

    def _synthesize(self, query: str, evidence: list[Evidence]) -> str:
        citations = "\n".join(
            f"- {item.chunk.source}: {item.chunk.text[:400]}" for item in evidence
        )
        prompt = (
            "You are a research assistant. Answer the query using only the evidence. "
            "Cite sources by filename."
        )
        return self._ask_llm(prompt, f"Query: {query}\nEvidence:\n{citations}\n")

    def research(self, query: str, chunks: list[Document]) -> str:
        return self._recursive_research(query, chunks, depth=0)

    def _recursive_research(self, query: str, chunks: list[Document], depth: int) -> str:
        evidence = self._score_chunks(query, chunks)
        answer = self._synthesize(query, evidence)
        if depth >= self.max_depth:
            return answer
        followups = self._plan_followups(query, evidence)
        if not followups:
            return answer
        followup_answers = []
        for followup in followups:
            followup_answers.append(self._recursive_research(followup, chunks, depth + 1))
        return answer + "\n\nFollow-up findings:\n" + "\n".join(followup_answers)
