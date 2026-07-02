import unittest
from unittest import mock

from docalyzer.ai_errors import AIConfigurationError, AISummarizationError
from docalyzer.ai_types import SummaryRequest
from docalyzer.model_enum import ModelEnum
from docalyzer.outupt_enum import OutputEnum
from docalyzer.provider_enum import ProviderEnum
from docalyzer.summarizer import shorten_title, summarize_long_text, summarize_text


class SummarizerTest(unittest.TestCase):
    def test_summarize_text_short(self) -> None:
        text = "This is sentence one. This is sentence two. This is sentence three."
        summary = summarize_text(text, max_sentences=2)
        self.assertGreaterEqual(summary.count("."), 2)
        self.assertIn("sentence one", summary)

    def test_summarize_long_text_chunks(self) -> None:
        text = "A." * 5000
        summary = summarize_long_text(text, chunk_size=1000, max_sentences=3)
        self.assertIsInstance(summary, str)

    def test_summarize_text_empty_content(self) -> None:
        self.assertEqual(summarize_text("   "), "No readable content found.")

    def test_shorten_title(self) -> None:
        self.assertEqual(shorten_title("hello_world-file"), "hello world file")

    @mock.patch("docalyzer.summarizer.create_ai_client")
    def test_summarize_long_text_uses_gemini_provider_for_legacy_flag(
        self, mock_create_ai_client: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize_request.return_value = "AI summary"
        mock_create_ai_client.return_value = mock_client

        summary = summarize_long_text("Long text", use_gemini=True)

        self.assertEqual(summary, "AI summary")
        mock_create_ai_client.assert_called_once_with(
            ProviderEnum.GEMINI,
            model_kind=None,
        )
        request = mock_client.summarize_request.call_args.args[0]
        self.assertEqual(
            request,
            SummaryRequest(
                text="Long text",
                max_sentences=5,
                output_format=OutputEnum.PLAIN,
                tofile_path=None,
                description_level=2,
                summary_level=2,
            ),
        )

    @mock.patch("docalyzer.summarizer.create_ai_client")
    def test_summarize_long_text_uses_selected_provider_and_model_kind(
        self, mock_create_ai_client: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize_request.return_value = "AI summary"
        mock_create_ai_client.return_value = mock_client

        summarize_long_text(
            "Long text",
            provider=ProviderEnum.OPENAI,
            model_kind=ModelEnum.HIGH,
        )

        mock_create_ai_client.assert_called_once_with(
            ProviderEnum.OPENAI,
            model_kind=ModelEnum.HIGH,
        )

    @mock.patch("docalyzer.summarizer.create_ai_client")
    def test_summarize_long_text_passes_request_options_to_ai_client(
        self, mock_create_ai_client: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize_request.return_value = "AI summary"
        mock_create_ai_client.return_value = mock_client

        summary = summarize_long_text(
            "Long text",
            provider=ProviderEnum.GEMINI,
            max_sentences=7,
            output_format=OutputEnum.JSON,
            tofile_path=mock.sentinel.output_path,
            description_level=3,
            summary_level=1,
        )

        self.assertEqual(summary, "AI summary")
        request = mock_client.summarize_request.call_args.args[0]
        self.assertEqual(
            request,
            SummaryRequest(
                text="Long text",
                max_sentences=7,
                output_format=OutputEnum.JSON,
                tofile_path=mock.sentinel.output_path,
                description_level=3,
                summary_level=1,
            ),
        )

    @mock.patch("docalyzer.summarizer.create_ai_client")
    def test_summarize_long_text_returns_provider_configuration_error(
        self, mock_create_ai_client: mock.Mock
    ) -> None:
        mock_create_ai_client.side_effect = AIConfigurationError("missing key")

        summary = summarize_long_text("Long text", provider=ProviderEnum.GEMINI)

        self.assertEqual(summary, "Gemini configuration error: missing key")

    @mock.patch("docalyzer.summarizer.create_ai_client")
    def test_summarize_long_text_returns_provider_api_error(
        self, mock_create_ai_client: mock.Mock
    ) -> None:
        mock_create_ai_client.side_effect = AISummarizationError("rate limited")

        summary = summarize_long_text("Long text", provider=ProviderEnum.OPENAI)

        self.assertEqual(summary, "OpenAI summarization failed: rate limited")

    def test_summarize_long_text_rejects_conflicting_provider_and_legacy_flag(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            summarize_long_text(
                "Long text",
                provider=ProviderEnum.OPENAI,
                use_gemini=True,
            )


if __name__ == "__main__":
    unittest.main()
