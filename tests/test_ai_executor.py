from __future__ import annotations

import unittest
from pathlib import Path

from docalyzer.ai_executor import AIExecutor
from docalyzer.ai_types import AIClient, SummaryRequest
from docalyzer.outupt_enum import OutputEnum


class DummyClient:
    def __init__(self) -> None:
        self.seen_request: SummaryRequest | None = None

    def summarize_request(self, request: SummaryRequest) -> str:
        self.seen_request = request
        return "delegated summary"


class NonClient:
    pass


class AIExecutorTest(unittest.TestCase):
    def test_executor_delegates_to_client_summarize_request(self) -> None:
        request = SummaryRequest(
            text="Long text",
            max_sentences=7,
            output_format=OutputEnum.JSON,
            tofile_path=Path("summary.json"),
            description_level=3,
            summary_level=1,
        )
        client = DummyClient()

        result = AIExecutor(client).summarize(request)

        self.assertEqual(result, "delegated summary")
        self.assertEqual(client.seen_request, request)

    def test_protocol_runtime_check_accepts_matching_client_shape(self) -> None:
        self.assertIsInstance(DummyClient(), AIClient)

    def test_protocol_runtime_check_rejects_non_matching_client_shape(self) -> None:
        self.assertNotIsInstance(NonClient(), AIClient)


if __name__ == "__main__":
    unittest.main()
