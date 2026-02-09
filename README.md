# Azure Foundry Deep Research IC Agent

This repository contains a Python-based Azure Foundry agent that performs deep research reasoning over SharePoint diligence materials and an IC paper. The agent applies the IC Checklist framework, prioritizes external diligence materials, and produces a concise deal conviction assessment plus a diligence gap analysis.

## Capabilities

- Authenticates to Microsoft Graph to read SharePoint folder contents and download documents.
- Filters and ranks diligence evidence using the **most recent** rule with version-aware sorting.
- Enforces the requirement that both **IC Paper** and **Project Working Folder** are present before analysis.
- Constructs a recursive depth loop (plan → search → evaluate gaps → refine → repeat → synthesize → self-critique).
- Produces structured, decision-focused output for IC preparation.

## Quick Start

1. **Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment**

Copy `.env.example` to `.env` and fill in values.

3. **Run**

```bash
python main.py \
  --site-id "<sharepoint-site-id>" \
  --drive-id "<sharepoint-drive-id>" \
  --project-folder "Project Working Folder" \
  --ic-paper "IC Paper.pdf" \
  --max-iterations 3
```

## Notes

- The agent expects that the IC Paper file exists in the project folder.
- External diligence sources are prioritized over Morrison-branded materials.
- Most recent rule: version suffixes (e.g., `v3`, `final`) take precedence over modified date.
- The agent runs a recursive depth loop capped by `--max-iterations`, followed by synthesis and self-critique.
- Documents are parsed (PDF/DOCX/XLSX/TXT) and chunked for content-based search.

## Files

- `main.py` - CLI entry point.
- `src/agent.py` - Azure Foundry agent orchestration.
- `src/content_index.py` - Text chunking and content search utilities.
- `src/document_parser.py` - Document content extraction helpers.
- `src/sharepoint_client.py` - Graph API SharePoint access.
- `src/document_selector.py` - Evidence selection and filtering logic.
- `src/prompt_builder.py` - Prompt creation using IC Checklist framework.
