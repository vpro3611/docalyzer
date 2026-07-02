from __future__ import annotations

from docalyzer.ai_types import AIClient, SummaryRequest


class AIExecutor:
    def __init__(self, client: AIClient) -> None:
        self.client = client

    def summarize(self, request: SummaryRequest) -> str:
        return self.client.summarize_request(request)
