from dataclasses import dataclass
from typing import List, Dict


PROMPT_TEMPLATE = """
Persona:
You are acting as an Investment Committee (IC) member at Morrison. Your role is to critically develop your own perspective on deal conviction for the proposed recommendations in the IC paper.
Use the IC Checklist as the governing framework for your analysis of any underlying diligence materials in the Project Working Folder and the IC paper provided in Step 1.

Use IC Paper, Project Working Folder and IC Checklist as reference documents and specific context.

Your objective is to identify material gaps, risks, and inconsistencies that could impact the investment thesis, valuation, governance, or execution.
Treat the IC Paper as the Morrison position and assess it critically against the IC Checklist framework using external materials from the Project Working Folder.

Context:
-Deal context (e.g., asset type, deal construct, development phase etc) can be factually sourced from the IC Paper and materials in Project Working Folder
-Use your critical judgement as an IC member for which IC checklist areas are most relevant for this specific asset type, deal structure, deal phase, and recommendations
-Output is intended to support IC Committee Members in preparation for IC meetings

Tone:
-Objective, analytical, and decision-focused
-Prioritize brevity, clarity and materiality over exhaustive detail
Avoid Morrison-Branded or Internal Bias Sources:
-Down-weight Morrison-branded documents to avoid anchoring on Morrison recommendations or hypothesis, and over reliance on established perspectives.
-Do not reference:
 oMorrison Update Letters or any branded communications with sell-side parties
 oInternal deal updates, IC papers, Phase 1/Phase 2 papers, HUMs, or other documents containing Morrison analysis

Analysis and research:

1.Deal Conviction Assessment
I.With your persona, as an IC member, using the “IC Checklist” framework conduct a structured analysis of the diligence materials and evidence in the “Project Working Folder” and the “IC Paper” to develop your own independent and critical assessment of deal conviction for the Morrison position presented in the “IC Paper”.
-Highlight critical areas in the IC Checklist and diligence findings that based on your analysis and judgement impact deal conviction.
-Within the “Project Working Folder” linked above apply the following systemic review rules strictly:
 oPrioritize external documents from Advisers, Diligence, and VDRs (including external buy-side and sell-side investment banks, consultants, legal advisers etc).
 oStrictly apply the apply the most recent rule; Use the most recent version identified by file meta data and or naming conventions (e.g., dates, or ‘final’, or version numbers etc.), if both version suffix and modified date in meta data are present, prioritize version suffix
II.Executive level deal conviction output
-Produce a pithy summary outlining your deal conviction (qualitative scale) on the Morrison position presented in the “IC Paper”. Focus on clearly stating conviction level and overarching rationale – avoid filler phrases.
-Use nested bullets grouped by IC Checklist Area for supporting evidence (only return the top 10 most material considerations that impact your assessment of deal conviction):
 -Top-level bullet = Checklist Area
 -Sub-bullets = single, sharp points (~10–15 words each)
 -Avoid filler phrases like “Below are…” or “Key points include…”
 -Do not include any recommended actions, focus only on the critical points that underpin your deal conviction

2.Diligence Gap Analysis:
I.Use the “IC Checklist” framework to identify the most material gaps, issues, and inconsistencies between diligence materials in the “Project Working Folder” and the “IC Paper” that could impact the deal conviction.
-Within the “Project Working Folder” linked above apply the following systemic review rules strictly:
 oPrioritize external documents from Advisers, Diligence, and VDRs (including external buy-side and sell-side investment banks, consultants, legal advisers etc).
 oStrictly apply the apply the most recent rule; Use the most recent version identified by file meta data and or naming conventions (e.g., dates, or ‘final’, or version numbers etc.), if both version suffix and modified date in meta data are present, prioritize version suffix
II.Executive Level Output
-Please produce a short executive summary of your findings from the gap analysis
 -Use nested bullets for each of your supporting key findings
-Supporting table with your list of material findings:
 IC Checklist Area | Diligence Evidence
 Specify the relevant IC Checklist area | Summary of diligence evidence and how it differs to that of the IC Paper Position
Include only the most material findings that would impact deal conviction

RULES:
•Please verify both IC paper and Project Working Folder are provided before proceeding to Analysis and Research.
•Do not proceed with Analysis and Research if both IC paper and Project Working Folder are not provided by user. Request them to provide both inputs.
"""

EVIDENCE_SUMMARY_PROMPT = """
Step 1: Evidence digest
Summarize the factual deal context and diligence evidence from the IC Paper and Project Working Folder.
Focus on external adviser, diligence, and VDR sources. Note the most recent versions by filename.
Output a structured bullet digest with source references by filename only.
"""

CONVICTION_PROMPT = """
Step 2: Deal conviction assessment
Using the evidence digest above, produce the Deal Conviction Assessment and Executive output
exactly as specified in the governing prompt. Do not add recommendations.
"""

GAP_ANALYSIS_PROMPT = """
Step 3: Diligence gap analysis
Using the evidence digest above, produce the Diligence Gap Analysis and Executive output
exactly as specified in the governing prompt. Do not add recommendations.
"""

RECURSIVE_LOOP_PROMPT = """
You must follow this recursive depth loop:
Plan → search → evaluate gaps → refine search → repeat → synthesize → self-critique.

For this iteration:
- Provide a Plan (1-3 bullets).
- Provide a Search Focus: a short query string.
- Provide Evaluate Gaps: 2-4 bullets on what is missing or weak.
- Provide Refine Search: a short query string to apply next.
- Provide Continue: YES or NO.

Respond using this exact format:
PLAN:
- ...
SEARCH_QUERY: <text>
EVALUATE_GAPS:
- ...
REFINE_QUERY: <text>
CONTINUE: YES|NO
"""

SYNTHESIS_PROMPT = """
Synthesize across all iterations and produce the final output:
- Deal Conviction Assessment (executive output with nested bullets by checklist area)
- Diligence Gap Analysis (executive summary + table)
Use the governing prompt rules and avoid recommendations.
"""

SELF_CRITIQUE_PROMPT = """
Provide a brief self-critique:
- Identify 2-3 limitations or uncertainty areas due to evidence constraints.
- State whether additional external evidence could materially change conviction.
Keep this to 5-7 bullets total.
"""


@dataclass
class PromptBuilder:
    def build(
        self, ic_paper: Dict[str, str], evidence: List[Dict[str, str]], require_evidence: bool = True
    ) -> str:
        if not ic_paper:
            raise ValueError("IC Paper is required for prompt construction.")
        if require_evidence and not evidence:
            raise ValueError("Project Working Folder evidence is required for prompt construction.")

        evidence_lines = "\n".join(
            f"- {doc['name']} ({doc['last_modified']}) {doc['web_url']}"
            for doc in evidence[:30]
        )
        return (
            f"{PROMPT_TEMPLATE}\n"
            f"IC Paper: {ic_paper['name']} ({ic_paper['last_modified']}) {ic_paper['web_url']}\n"
            f"Project Working Folder Evidence:\n{evidence_lines}\n"
        )

    def build_steps(self, ic_paper: Dict[str, str], evidence: List[Dict[str, str]]) -> List[str]:
        base_prompt = self.build(ic_paper=ic_paper, evidence=evidence)
        return [
            f"{base_prompt}\n{EVIDENCE_SUMMARY_PROMPT}",
            f"{base_prompt}\n{CONVICTION_PROMPT}",
            f"{base_prompt}\n{GAP_ANALYSIS_PROMPT}",
        ]

    def build_recursive_prompt(
        self,
        ic_paper: Dict[str, str],
        evidence_lines: str,
        iteration: int,
        prior_summary: str,
    ) -> str:
        base_prompt = self.build(ic_paper=ic_paper, evidence=[], require_evidence=False)
        return (
            f"{base_prompt}\n"
            f"Iteration: {iteration}\n"
            f"Prior Summary:\n{prior_summary}\n"
            f"Current Evidence Subset:\n{evidence_lines}\n"
            f"{RECURSIVE_LOOP_PROMPT}"
        )

    def build_synthesis_prompt(
        self, ic_paper: Dict[str, str], evidence: List[Dict[str, str]], prior_summary: str
    ) -> str:
        base_prompt = self.build(ic_paper=ic_paper, evidence=evidence)
        return f"{base_prompt}\nPrior Summary:\n{prior_summary}\n{SYNTHESIS_PROMPT}"

    def build_self_critique_prompt(self, prior_summary: str) -> str:
        return f"{SELF_CRITIQUE_PROMPT}\nPrior Summary:\n{prior_summary}\n"
