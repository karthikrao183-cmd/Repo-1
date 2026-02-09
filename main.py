import argparse
import os
from typing import List

from dotenv import load_dotenv

from src.agent import FoundryICAgent
from src.sharepoint_client import SharePointClient
from src.document_selector import DocumentSelector
from src.prompt_builder import PromptBuilder
from src.document_parser import parse_document, ParsedDocument
from src.content_index import ContentChunk, chunk_text, search_chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Azure Foundry IC deep research agent")
    parser.add_argument("--site-id", required=True, help="SharePoint site ID")
    parser.add_argument("--drive-id", required=True, help="SharePoint drive ID")
    parser.add_argument(
        "--project-folder",
        required=True,
        help="Project Working Folder path or name",
    )
    parser.add_argument(
        "--ic-paper",
        required=True,
        help="IC Paper filename expected inside Project Working Folder",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum recursive depth iterations",
    )
    return parser.parse_args()


def parse_loop_response(response: str) -> tuple[bool, str]:
    continue_flag = True
    refine_query = ""
    for line in response.splitlines():
        if line.strip().startswith("CONTINUE:"):
            value = line.split(":", 1)[1].strip().upper()
            continue_flag = value == "YES"
        if line.strip().startswith("REFINE_QUERY:"):
            refine_query = line.split(":", 1)[1].strip()
    return continue_flag, refine_query


def build_content_index(parsed_docs: List[ParsedDocument]) -> List[ContentChunk]:
    chunks: List[ContentChunk] = []
    for parsed in parsed_docs:
        for idx, chunk in enumerate(chunk_text(parsed.text), start=1):
            chunks.append(ContentChunk(doc_name=parsed.name, chunk_id=idx, text=chunk))
    return chunks


def main() -> None:
    load_dotenv()
    args = parse_args()

    sharepoint = SharePointClient(
        tenant_id=os.environ.get("AZURE_TENANT_ID", ""),
        client_id=os.environ.get("AZURE_CLIENT_ID", ""),
        client_secret=os.environ.get("AZURE_CLIENT_SECRET", ""),
    )

    documents = sharepoint.list_folder_documents(
        site_id=args.site_id,
        drive_id=args.drive_id,
        folder_path=args.project_folder,
    )

    selector = DocumentSelector()
    ic_paper, evidence = selector.select_documents(
        documents=documents,
        ic_paper_name=args.ic_paper,
    )

    all_docs = [ic_paper] + evidence
    parsed_docs: List[ParsedDocument] = []
    for doc in all_docs:
        content = sharepoint.download_file_content(
            site_id=args.site_id,
            drive_id=args.drive_id,
            item_id=doc["id"],
        )
        parsed = parse_document(doc["name"], content)
        if parsed.text:
            parsed_docs.append(parsed)

    content_chunks = build_content_index(parsed_docs)

    prompt_builder = PromptBuilder()
    agent = FoundryICAgent(
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
        ai_project_connection=os.environ.get("AZURE_AI_PROJECT_CONNECTION", ""),
    )

    prior_summary = ""
    search_query = ""
    for iteration in range(1, args.max_iterations + 1):
        matched_chunks = search_chunks(content_chunks, search_query, limit=20)
        evidence_lines = "\n".join(
            f"- {chunk.doc_name} [chunk {chunk.chunk_id}]: {chunk.text[:300]}"
            for chunk in matched_chunks
        )
        loop_prompt = prompt_builder.build_recursive_prompt(
            ic_paper=ic_paper,
            evidence_lines=evidence_lines,
            iteration=iteration,
            prior_summary=prior_summary,
        )
        loop_response = agent.run(loop_prompt)
        print(f"\n--- Iteration {iteration} ---\n{loop_response}")
        prior_summary = f"{prior_summary}\n\nIteration {iteration}:\n{loop_response}".strip()

        continue_flag, refine_query = parse_loop_response(loop_response)
        if not continue_flag:
            break
        search_query = refine_query

    synthesis_prompt = prompt_builder.build_synthesis_prompt(
        ic_paper=ic_paper, evidence=evidence, prior_summary=prior_summary
    )
    synthesis_response = agent.run(synthesis_prompt)
    print(f"\n--- Synthesis ---\n{synthesis_response}")

    critique_prompt = prompt_builder.build_self_critique_prompt(prior_summary=prior_summary)
    critique_response = agent.run(critique_prompt)
    print(f"\n--- Self-Critique ---\n{critique_response}")


if __name__ == "__main__":
    main()
