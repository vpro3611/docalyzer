import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from docalyzer.gemini_client import DEFAULT_MODEL, GeminiAPIError, GeminiClient
from docalyzer.outupt_enum import OutputEnum


class TestGeminiClient(unittest.TestCase):
    """Test GeminiClient initialization and error handling."""

    def setUp(self) -> None:
        self.api_key = "test_api_key"
        self.model = "gemini-2.5-flash"

    @mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_from_env_loads_api_key(self) -> None:
        client = GeminiClient.from_env()
        self.assertEqual(client.api_key, "test_key")
        # self.assertEqual(client.model, self.model)

    @mock.patch("docalyzer.gemini_client._load_dotenv_file")
    def test_from_env_raises_on_missing_api_key(
        self, mock_load_dotenv: mock.Mock
    ) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                GeminiClient.from_env()
            self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    @mock.patch.dict(
        os.environ, {"GEMINI_API_KEY": "test_key", "GEMINI_MODEL": "custom-model"}
    )
    def test_from_env_loads_custom_model(self) -> None:
        client = GeminiClient.from_env()
        self.assertEqual(client.model, "custom-model")

    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_success(self, mock_genai_client: mock.Mock) -> None:
        mock_response = mock.Mock()
        mock_response.text = "Summary of the text."
        mock_genai_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        client = GeminiClient(api_key=self.api_key)
        result = client.summarize("This is a long text.", max_sentences=2)

        self.assertEqual(result, "Summary of the text.")
        mock_genai_client.return_value.models.generate_content.assert_called_once()

    def test_format_request_plain_includes_plain_text_rules(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        prompt = client._format_request(
            "This is a long text.", OutputEnum.PLAIN, max_sentences=2
        )

        self.assertIn("professional plain text format", prompt)
        self.assertIn("do not use Markdown syntax or JSON", prompt)
        self.assertIn("no more than 2 sentences", prompt)
        self.assertIn("The output format must be txt", prompt)
        self.assertIn("Text:\n\nThis is a long text.", prompt)

    def test_format_request_markdown_includes_markdown_rules(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        prompt = client._format_request(
            "This is a long text.", OutputEnum.MARKDOWN, max_sentences=3
        )

        self.assertIn("professional Markdown format", prompt)
        self.assertIn("proper Markdown headers and bullet points", prompt)
        self.assertIn("no more than 3 sentences", prompt)
        self.assertIn("The output format must be md", prompt)

    def test_format_request_json_includes_json_schema_rules(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        prompt = client._format_request(
            "This is a long text.", OutputEnum.JSON, max_sentences=4
        )

        self.assertIn("Return only valid JSON", prompt)
        self.assertIn("Use snake_case for all keys", prompt)
        self.assertIn("document_title", prompt)
        self.assertIn("short_description", prompt)
        self.assertIn("short_summary", prompt)
        self.assertIn("full_summary", prompt)
        self.assertIn("maximum of 4 sentences", prompt)

    def test_format_request_unknown_output_falls_back_to_plain_text(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        with mock.patch("builtins.print") as mock_print:
            prompt = client._format_request("This is a long text.", "yaml", 2)

        self.assertIn("professional plain text format", prompt)
        self.assertIn("If the requested format is unknown", prompt)
        mock_print.assert_called_once()

    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_raises_on_missing_text(
        self, mock_genai_client: mock.Mock
    ) -> None:
        mock_response = mock.Mock(spec=[])
        mock_genai_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        client = GeminiClient(api_key=self.api_key)
        with self.assertRaises(GeminiAPIError) as ctx:
            client.summarize("This is a long text.")
        self.assertIn("without text field", str(ctx.exception))
        # Validation errors should not be retried
        self.assertEqual(
            mock_genai_client.return_value.models.generate_content.call_count, 1
        )

    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_raises_on_empty_text(self, mock_genai_client: mock.Mock) -> None:
        mock_response = mock.Mock()
        mock_response.text = "   "
        mock_genai_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        client = GeminiClient(api_key=self.api_key)
        with self.assertRaises(GeminiAPIError) as ctx:
            client.summarize("This is a long text.")
        self.assertIn("empty text", str(ctx.exception))
        # Validation errors should not be retried
        self.assertEqual(
            mock_genai_client.return_value.models.generate_content.call_count, 1
        )

    @mock.patch("docalyzer.gemini_client.time.sleep")
    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_retries_on_api_error(
        self, mock_genai_client: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock()
        mock_response.text = "Successful summary."

        # Create exception instances that match genai_errors behavior
        mock_genai_client.return_value.models.generate_content.side_effect = [
            RuntimeError("Server error"),
            RuntimeError("Client error"),
            mock_response,
        ]

        client = GeminiClient(api_key=self.api_key, max_retries=3)
        result = client.summarize("This is a long text.")

        self.assertEqual(result, "Successful summary.")
        self.assertEqual(
            mock_genai_client.return_value.models.generate_content.call_count, 3
        )
        self.assertEqual(mock_sleep.call_count, 2)

    @mock.patch("docalyzer.gemini_client.time.sleep")
    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_exponential_backoff(
        self, mock_genai_client: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_genai_client.return_value.models.generate_content.side_effect = [
            RuntimeError("Server error"),
            RuntimeError("Client error"),
            RuntimeError("API error"),
        ]

        client = GeminiClient(
            api_key=self.api_key, max_retries=3, initial_retry_delay=1.0
        )

        with self.assertRaises(GeminiAPIError):
            client.summarize("This is a long text.")

        expected_delays = [1.0, 2.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertEqual(actual_delays, expected_delays)

    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_fails_after_max_retries(
        self, mock_genai_client: mock.Mock
    ) -> None:
        mock_genai_client.return_value.models.generate_content.side_effect = (
            RuntimeError("Persistent server error")
        )

        client = GeminiClient(api_key=self.api_key, max_retries=2)

        with self.assertRaises(GeminiAPIError) as ctx:
            client.summarize("This is a long text.")

        self.assertIn("after 2 retries", str(ctx.exception))
        self.assertEqual(
            mock_genai_client.return_value.models.generate_content.call_count, 2
        )

    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_handles_generic_error(
        self, mock_genai_client: mock.Mock
    ) -> None:
        mock_response = mock.Mock()
        mock_response.text = "Recovered from error."

        mock_genai_client.return_value.models.generate_content.side_effect = [
            RuntimeError("Generic error"),
            mock_response,
        ]

        client = GeminiClient(api_key=self.api_key, max_retries=2)

        result = client.summarize("This is a long text.")

        self.assertEqual(result, "Recovered from error.")
        self.assertEqual(
            mock_genai_client.return_value.models.generate_content.call_count, 2
        )

    def test_client_initialization_with_custom_retry_settings(self) -> None:
        client = GeminiClient(
            api_key=self.api_key, max_retries=5, initial_retry_delay=2.0
        )

        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.initial_retry_delay, 2.0)

    @mock.patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "test_key", "GEMINI_MAX_RETRIES": "5"},
    )
    def test_from_env_loads_max_retries(self) -> None:
        client = GeminiClient.from_env(max_retries=3)
        self.assertEqual(client.max_retries, 5)

    @mock.patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test_key",
            "GEMINI_MODEL": "env-model",
        },
    )
    def test_from_env_explicit_model_overrides_env(self) -> None:
        client = GeminiClient.from_env(model="explicit-model")
        self.assertEqual(client.model, "explicit-model")

    @mock.patch("docalyzer.gemini_client._load_dotenv_file")
    @mock.patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test_key",
        },
        clear=True,
    )
    def test_from_env_uses_default_model(self, mock_load_dotenv: mock.Mock) -> None:
        client = GeminiClient.from_env()

        self.assertEqual(client.model, DEFAULT_MODEL)

    @mock.patch("docalyzer.gemini_client.time.sleep")
    def test_sleep_with_backoff(self, mock_sleep: mock.Mock) -> None:
        client = GeminiClient(
            api_key=self.api_key,
            initial_retry_delay=1.5,
        )

        client._sleep_with_backoff(0)
        client._sleep_with_backoff(1)
        client._sleep_with_backoff(2)

        expected = [1.5, 3.0, 6.0]
        actual = [call.args[0] for call in mock_sleep.call_args_list]

        self.assertEqual(actual, expected)

    def test_write_to_file_creates_parent_directories_and_writes_content(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "summary"
            client._write_to_file("Saved summary", output_path, OutputEnum.MARKDOWN)

            saved_path = output_path.with_suffix(".md")
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_text(encoding="utf-8"), "Saved summary")

    def test_write_to_file_rejects_mismatched_extension(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"
            with self.assertRaises(ValueError) as ctx:
                client._write_to_file("Saved summary", output_path, OutputEnum.PLAIN)

            self.assertIn("does not match requested format", str(ctx.exception))

    def test_write_to_file_strips_json_fences_and_pretty_prints_json(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"
            client._write_to_file(
                '```json\n{"document_title":"","full_summary":"hello"}\n```',
                output_path,
                OutputEnum.JSON,
            )

            saved_text = output_path.read_text(encoding="utf-8")
            self.assertNotIn("```", saved_text)
            self.assertIn('  "document_title": ""', saved_text)
            self.assertIn('  "full_summary": "hello"', saved_text)
            self.assertTrue(saved_text.endswith("\n"))

    def test_write_to_file_pretty_prints_unfenced_json(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"
            client._write_to_file(
                '{"document_title":"Doc","full_summary":"hello"}',
                output_path,
                OutputEnum.JSON,
            )

            saved_text = output_path.read_text(encoding="utf-8")
            self.assertIn('  "document_title": "Doc"', saved_text)
            self.assertIn('  "full_summary": "hello"', saved_text)
            self.assertTrue(saved_text.endswith("\n"))

    def test_write_to_file_keeps_invalid_json_content_without_fences(self) -> None:
        client = GeminiClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"
            client._write_to_file(
                '{"document_title": invalid json}',
                output_path,
                OutputEnum.JSON,
            )

            saved_text = output_path.read_text(encoding="utf-8")
            self.assertEqual(saved_text, '{"document_title": invalid json}')

    @mock.patch("docalyzer.gemini_client.genai.Client")
    def test_summarize_writes_to_file_when_tofile_path_is_provided(
        self, mock_genai_client: mock.Mock
    ) -> None:
        mock_response = mock.Mock()
        mock_response.text = "Summary of the text."
        mock_genai_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        client = GeminiClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary"
            result = client.summarize(
                "This is a long text.",
                output_format=OutputEnum.JSON,
                tofile_path=output_path,
            )

            self.assertEqual(result, "Summary of the text.")
            saved_path = output_path.with_suffix(".json")
            self.assertTrue(saved_path.exists())
            self.assertEqual(
                saved_path.read_text(encoding="utf-8"), "Summary of the text."
            )


if __name__ == "__main__":
    unittest.main()
