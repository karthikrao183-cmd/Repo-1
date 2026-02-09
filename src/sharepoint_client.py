from dataclasses import dataclass
from typing import List, Dict

import msal
import requests


@dataclass
class SharePointClient:
    tenant_id: str
    client_id: str
    client_secret: str

    def _get_token(self) -> str:
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Tenant, client ID, and client secret are required.")
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError("Failed to acquire Microsoft Graph access token.")
        return result["access_token"]

    def list_folder_documents(self, site_id: str, drive_id: str, folder_path: str) -> List[Dict[str, str]]:
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}"
            f"/drives/{drive_id}/root:/{folder_path}:/children"
        )
        items: List[Dict[str, str]] = []
        while url:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            for item in data.get("value", []):
                if "file" in item:
                    items.append(
                        {
                            "name": item.get("name", ""),
                            "id": item.get("id", ""),
                            "last_modified": item.get("lastModifiedDateTime", ""),
                            "web_url": item.get("webUrl", ""),
                        }
                    )
            url = data.get("@odata.nextLink")
        return items

    def download_file_content(self, site_id: str, drive_id: str, item_id: str) -> bytes:
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}"
            f"/drives/{drive_id}/items/{item_id}/content"
        )
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.content
