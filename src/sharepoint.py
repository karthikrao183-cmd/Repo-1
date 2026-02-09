from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import msal
import requests

from .document_loader import Document


@dataclass(frozen=True)
class SharePointFile:
    file_id: str
    name: str
    download_url: str


def _get_graph_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Failed to get Graph token: {result}")
    return result["access_token"]


def list_sharepoint_files(
    *,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    site_id: str,
    drive_id: str,
) -> list[SharePointFile]:
    token = _get_graph_token(tenant_id, client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    items = response.json().get("value", [])
    files: list[SharePointFile] = []
    for item in items:
        if "file" not in item:
            continue
        files.append(
            SharePointFile(
                file_id=item["id"],
                name=item["name"],
                download_url=item["@microsoft.graph.downloadUrl"],
            )
        )
    return files


def download_sharepoint_documents(
    *,
    files: Iterable[SharePointFile],
) -> list[Document]:
    documents: list[Document] = []
    for file in files:
        response = requests.get(file.download_url, timeout=60)
        response.raise_for_status()
        text = response.text
        if not text.strip():
            continue
        documents.append(
            Document(
                doc_id=file.file_id,
                source=f"sharepoint:{file.name}",
                text=text,
                metadata={"filename": file.name},
            )
        )
    return documents
