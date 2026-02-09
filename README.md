# Azure AI Foundry Recursive Cognitive Research Agent

This sample shows how to build a **recursive cognitive agent** using Azure AI Foundry (Azure AI Projects + Azure OpenAI) that can run deep research over SharePoint documents or locally uploaded files.

The agent:
- Pulls documents from SharePoint via Microsoft Graph, or loads local files.
- Splits content into chunks and generates embeddings.
- Recursively plans follow-up questions, retrieves evidence, and synthesizes a final answer.

## Prerequisites

- Python 3.10+
- Azure AI Foundry project with an Azure OpenAI deployment
- (Optional) Azure AI Search index if you want server-side vector search
- SharePoint app registration in Entra ID for Graph API access

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file or export environment variables:

```bash
export AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-large"
export AZURE_OPENAI_API_KEY="YOUR-OPENAI-API-KEY"

# Optional Azure AI Search
export AZURE_AI_SEARCH_ENDPOINT="https://YOUR-SEARCH.search.windows.net"
export AZURE_AI_SEARCH_KEY="YOUR-SEARCH-ADMIN-KEY"
export AZURE_AI_SEARCH_INDEX="research-index"

# SharePoint / Graph settings
export SHAREPOINT_TENANT_ID="YOUR-TENANT-ID"
export SHAREPOINT_CLIENT_ID="YOUR-CLIENT-ID"
export SHAREPOINT_CLIENT_SECRET="YOUR-CLIENT-SECRET"
export SHAREPOINT_SITE_ID="YOUR-SITE-ID"
export SHAREPOINT_DRIVE_ID="YOUR-DRIVE-ID"
```

## Run with local documents

```bash
python -m src.main --query "Summarize Q2 revenue risks" --local-path ./docs
```

## Run with SharePoint documents

```bash
python -m src.main --query "What are the top security findings?" --sharepoint
```

## Notes

- This sample uses recursive depth to generate follow-up questions and refine answers.
- The agent can be extended to store embeddings in Azure AI Search for larger document sets.
- SharePoint access uses client credentials flow with Microsoft Graph.
