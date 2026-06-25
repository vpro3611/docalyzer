import unittest
from unittest import mock

from docalyzer.gemini_client import DEFAULT_MODEL, GeminiAPIError
from docalyzer.model_enum import MODEL_MAP, ModelEnum
from docalyzer.outupt_enum import OutputEnum
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

    @mock.patch("docalyzer.gemini_client.GeminiClient.from_env")
    def test_summarize_long_text_uses_default_model_for_gemini(
        self, mock_from_env: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize.return_value = "AI summary"
        mock_from_env.return_value = mock_client

        summary = summarize_long_text("Long text", use_gemini=True)

        self.assertEqual(summary, "AI summary")
        mock_from_env.assert_called_once_with(model=DEFAULT_MODEL)
        mock_client.summarize.assert_called_once_with(
            "Long text", max_sentences=5, output_format=OutputEnum.PLAIN
        )

    @mock.patch("docalyzer.gemini_client.GeminiClient.from_env")
    def test_summarize_long_text_uses_selected_model_kind_for_gemini(
        self, mock_from_env: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize.return_value = "AI summary"
        mock_from_env.return_value = mock_client

        summarize_long_text("Long text", model_kind=ModelEnum.HIGH, use_gemini=True)

        mock_from_env.assert_called_once_with(model=MODEL_MAP[ModelEnum.HIGH])
        mock_client.summarize.assert_called_once_with(
            "Long text", max_sentences=5, output_format=OutputEnum.PLAIN
        )

    @mock.patch("docalyzer.gemini_client.GeminiClient.from_env")
    def test_summarize_long_text_passes_selected_output_format_to_gemini(
        self, mock_from_env: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize.return_value = "AI markdown summary"
        mock_from_env.return_value = mock_client

        summary = summarize_long_text(
            "Long text", use_gemini=True, output_format=OutputEnum.MARKDOWN
        )

        self.assertEqual(summary, "AI markdown summary")
        mock_from_env.assert_called_once_with(model=DEFAULT_MODEL)
        mock_client.summarize.assert_called_once_with(
            "Long text", max_sentences=5, output_format=OutputEnum.MARKDOWN
        )

    @mock.patch("docalyzer.gemini_client.GeminiClient.from_env")
    def test_summarize_long_text_returns_gemini_configuration_error(
        self, mock_from_env: mock.Mock
    ) -> None:
        mock_from_env.side_effect = ValueError("missing key")

        summary = summarize_long_text("Long text", use_gemini=True)

        self.assertEqual(summary, "Gemini configuration error: missing key")

    @mock.patch("docalyzer.gemini_client.GeminiClient.from_env")
    def test_summarize_long_text_returns_gemini_api_error(
        self, mock_from_env: mock.Mock
    ) -> None:
        mock_client = mock.Mock()
        mock_client.summarize.side_effect = GeminiAPIError("rate limited")
        mock_from_env.return_value = mock_client

        summary = summarize_long_text("Long text", use_gemini=True)

        self.assertEqual(summary, "Gemini summarization failed: rate limited")


if __name__ == "__main__":
    unittest.main()
