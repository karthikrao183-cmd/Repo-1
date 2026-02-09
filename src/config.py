from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AzureOpenAIConfig:
    endpoint: str
    deployment: str
    api_version: str
    embedding_deployment: str
    api_key: str | None


@dataclass(frozen=True)
class AzureSearchConfig:
    endpoint: str
    api_key: str
    index_name: str


@dataclass(frozen=True)
class SharePointConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    site_id: str
    drive_id: str


def load_openai_config() -> AzureOpenAIConfig:
    return AzureOpenAIConfig(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        embedding_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    )


def load_search_config() -> AzureSearchConfig | None:
    endpoint = os.environ.get("AZURE_AI_SEARCH_ENDPOINT")
    api_key = os.environ.get("AZURE_AI_SEARCH_KEY")
    index_name = os.environ.get("AZURE_AI_SEARCH_INDEX")
    if not endpoint or not api_key or not index_name:
        return None
    return AzureSearchConfig(endpoint=endpoint, api_key=api_key, index_name=index_name)


def load_sharepoint_config() -> SharePointConfig:
    return SharePointConfig(
        tenant_id=os.environ["SHAREPOINT_TENANT_ID"],
        client_id=os.environ["SHAREPOINT_CLIENT_ID"],
        client_secret=os.environ["SHAREPOINT_CLIENT_SECRET"],
        site_id=os.environ["SHAREPOINT_SITE_ID"],
        drive_id=os.environ["SHAREPOINT_DRIVE_ID"],
    )
