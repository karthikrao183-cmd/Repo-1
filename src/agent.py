from dataclasses import dataclass
from typing import Any, List

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


@dataclass
class FoundryICAgent:
    endpoint: str
    deployment: str
    ai_project_connection: str

    def run(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Prompt is required.")
        if not self.ai_project_connection:
            raise ValueError("AZURE_AI_PROJECT_CONNECTION is required.")
        if not self.endpoint or not self.deployment:
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT are required.")

        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        project_client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=self.ai_project_connection,
        )

        chat_client = project_client.get_chat_completions_client()
        response: Any = chat_client.complete(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an Azure Foundry IC reasoning agent."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content

    def run_multi(self, prompts: List[str]) -> List[str]:
        if not prompts:
            raise ValueError("At least one prompt is required.")
        responses: List[str] = []
        context: List[dict[str, str]] = [
            {"role": "system", "content": "You are an Azure Foundry IC reasoning agent."}
        ]

        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        project_client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=self.ai_project_connection,
        )
        chat_client = project_client.get_chat_completions_client()

        for prompt in prompts:
            if not prompt.strip():
                raise ValueError("Prompt is required.")
            context.append({"role": "user", "content": prompt})
            response: Any = chat_client.complete(
                model=self.deployment,
                messages=context,
                temperature=0.2,
            )
            message = response.choices[0].message.content
            context.append({"role": "assistant", "content": message})
            responses.append(message)
        return responses
