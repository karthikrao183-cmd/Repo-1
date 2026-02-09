from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .config import load_openai_config, load_sharepoint_config
from .document_loader import chunk_documents, load_local_documents
from .research_agent import RecursiveResearchAgent
from .sharepoint import download_sharepoint_documents, list_sharepoint_files


def _load_documents(args: argparse.Namespace):
    if args.sharepoint:
        sp_config = load_sharepoint_config()
        files = list_sharepoint_files(
            tenant_id=sp_config.tenant_id,
            client_id=sp_config.client_id,
            client_secret=sp_config.client_secret,
            site_id=sp_config.site_id,
            drive_id=sp_config.drive_id,
        )
        return download_sharepoint_documents(files=files)
    if args.local_path:
        return load_local_documents(Path(args.local_path))
    raise ValueError("Provide --sharepoint or --local-path")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Recursive research agent")
    parser.add_argument("--query", required=True, help="Research question")
    parser.add_argument("--sharepoint", action="store_true", help="Use SharePoint documents")
    parser.add_argument("--local-path", help="Local directory with uploaded docs")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--max-evidence", type=int, default=6)
    args = parser.parse_args()

    documents = _load_documents(args)
    chunks = chunk_documents(documents, chunk_size=args.chunk_size, overlap=args.chunk_overlap)

    openai_config = load_openai_config()
    agent = RecursiveResearchAgent(
        openai_config=openai_config,
        max_depth=args.max_depth,
        max_evidence=args.max_evidence,
    )
    response = agent.research(args.query, chunks)
    print(response)


if __name__ == "__main__":
    main()
