from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import docalyzer.openai_client as openai_client_module
from docalyzer.openai_client import DEFAULT_MODEL, OpenAIAPIError, OpenAIClient
from docalyzer.outupt_enum import OutputEnum


class RateLimitError(Exception):
    pass


class APITimeoutError(Exception):
    pass


class APIConnectionError(Exception):
    pass


class APIStatusError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class APIError(Exception):
    pass


class TestOpenAIClient(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = "test_api_key"
        self.model = DEFAULT_MODEL

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_from_env_loads_api_key(self, mock_openai: mock.Mock) -> None:
        client = OpenAIClient.from_env()
        self.assertEqual(client.api_key, "test_key")
        mock_openai.assert_called_once()

    @mock.patch("docalyzer.openai_client._load_dotenv_file")
    def test_from_env_raises_on_missing_api_key(
        self, mock_load_dotenv: mock.Mock
    ) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                OpenAIClient.from_env()
            self.assertIn("OPENAI_API_KEY", str(ctx.exception))

    @mock.patch.dict(
        os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "custom-model"}
    )
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_from_env_loads_custom_model(self, mock_openai: mock.Mock) -> None:
        client = OpenAIClient.from_env()
        self.assertEqual(client.model, "custom-model")

    @mock.patch.dict(
        os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MAX_RETRIES": "5"}
    )
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_from_env_loads_max_retries(self, mock_openai: mock.Mock) -> None:
        client = OpenAIClient.from_env(max_retries=2)

        self.assertEqual(client.max_retries, 5)

    @mock.patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "env-model"},
    )
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_from_env_explicit_model_overrides_env(
        self, mock_openai: mock.Mock
    ) -> None:
        client = OpenAIClient.from_env(model="explicit-model")

        self.assertEqual(client.model, "explicit-model")

    @mock.patch("docalyzer.openai_client._load_dotenv_file")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}, clear=True)
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_from_env_uses_default_model(
        self,
        mock_openai: mock.Mock,
        mock_load_dotenv: mock.Mock,
    ) -> None:
        client = OpenAIClient.from_env()

        self.assertEqual(client.model, DEFAULT_MODEL)

    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_summarize_success(self, mock_openai: mock.Mock) -> None:
        mock_response = mock.Mock()
        mock_response.output_text = "Summary of the text."
        mock_openai.return_value.responses.create.return_value = mock_response

        client = OpenAIClient(api_key=self.api_key)
        result = client.summarize("This is a long text.", max_sentences=2)

        self.assertEqual(result, "Summary of the text.")
        mock_openai.return_value.responses.create.assert_called_once()

    def test_format_request_plain_includes_plain_text_rules(self) -> None:
        with mock.patch("docalyzer.openai_client.openai_module.OpenAI"):
            client = OpenAIClient(api_key=self.api_key)

        prompt = client._format_request(
            "This is a long text.", OutputEnum.PLAIN, max_sentences=2
        )

        self.assertIn("professional plain text format", prompt)
        self.assertIn("Provide a detailed description of the given text.", prompt)
        self.assertIn(
            "The summary should be detailed, but still fit into the sentences cap.",
            prompt,
        )

    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_summarize_raises_on_missing_text(self, mock_openai: mock.Mock) -> None:
        mock_response = mock.Mock(spec=[])
        mock_openai.return_value.responses.create.return_value = mock_response

        client = OpenAIClient(api_key=self.api_key)
        with self.assertRaises(OpenAIAPIError) as ctx:
            client.summarize("This is a long text.")
        self.assertIn("without extractable text", str(ctx.exception))

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_summarize_retries_on_generic_error(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock()
        mock_response.output_text = "Recovered"
        mock_openai.return_value.responses.create.side_effect = [
            RuntimeError("temporary"),
            mock_response,
        ]

        client = OpenAIClient(api_key=self.api_key, max_retries=2)
        result = client.summarize("This is a long text.")

        self.assertEqual(result, "Recovered")
        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_extract_text_reads_output_text(self, mock_openai: mock.Mock) -> None:
        client = OpenAIClient(api_key=self.api_key)
        response = mock.Mock(output_text="  extracted text  ")

        result = client._extract_text(response)

        self.assertEqual(result, "extracted text")

    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_extract_text_falls_back_to_choice_text(
        self, mock_openai: mock.Mock
    ) -> None:
        client = OpenAIClient(api_key=self.api_key)
        choice = mock.Mock(text="  extracted text  ")
        response = mock.Mock(output_text=None, choices=[choice])

        result = client._extract_text(response)

        self.assertEqual(result, "extracted text")

    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_extract_text_falls_back_to_message_content(
        self, mock_openai: mock.Mock
    ) -> None:
        client = OpenAIClient(api_key=self.api_key)
        message = mock.Mock(content="  extracted text  ")
        choice = mock.Mock(text=None, message=message)
        response = mock.Mock(output_text=None, choices=[choice])

        result = client._extract_text(response)

        self.assertEqual(result, "extracted text")

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_retries_on_rate_limit_error(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock(output_text="ok")
        mock_openai.return_value.responses.create.side_effect = [
            RateLimitError("retry"),
            mock_response,
        ]

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=2)
            result = client.summarize("text")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_retries_on_api_timeout_error(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock(output_text="ok")
        mock_openai.return_value.responses.create.side_effect = [
            APITimeoutError("retry"),
            mock_response,
        ]

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=2)
            result = client.summarize("text")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_retries_on_api_connection_error(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock(output_text="ok")
        mock_openai.return_value.responses.create.side_effect = [
            APIConnectionError("retry"),
            mock_response,
        ]

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=2)
            result = client.summarize("text")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_retries_on_retryable_status_error(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock(output_text="ok")
        mock_openai.return_value.responses.create.side_effect = [
            APIStatusError("retry", status_code=500),
            mock_response,
        ]

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=2)
            result = client.summarize("text")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_retries_on_rate_limit_status_error(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_response = mock.Mock(output_text="ok")
        mock_openai.return_value.responses.create.side_effect = [
            APIStatusError("retry", status_code=429),
            mock_response,
        ]

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=2)
            result = client.summarize("text")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_non_retryable_status_error_raises_immediately(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_openai.return_value.responses.create.side_effect = APIStatusError(
            "bad request",
            status_code=400,
        )

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=3)
            with self.assertRaises(OpenAIAPIError):
                client.summarize("text")

        self.assertEqual(mock_openai.return_value.responses.create.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 0)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_retries_on_generic_api_error_until_exhausted(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        mock_openai.return_value.responses.create.side_effect = APIError("boom")

        with (
            mock.patch.object(
                openai_client_module.openai_module, "RateLimitError", RateLimitError
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APITimeoutError", APITimeoutError
            ),
            mock.patch.object(
                openai_client_module.openai_module,
                "APIConnectionError",
                APIConnectionError,
            ),
            mock.patch.object(
                openai_client_module.openai_module, "APIStatusError", APIStatusError
            ),
            mock.patch.object(openai_client_module.openai_module, "APIError", APIError),
        ):
            client = OpenAIClient(api_key=self.api_key, max_retries=2)
            with self.assertRaises(OpenAIAPIError):
                client.summarize("text")

        self.assertEqual(mock_openai.return_value.responses.create.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("docalyzer.openai_client.time.sleep")
    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_sleep_with_backoff_uses_exponential_delays(
        self, mock_openai: mock.Mock, mock_sleep: mock.Mock
    ) -> None:
        client = OpenAIClient(
            api_key=self.api_key,
            initial_retry_delay=1.5,
        )

        client._sleep_with_backoff(0)
        client._sleep_with_backoff(1)
        client._sleep_with_backoff(2)

        actual = [call.args[0] for call in mock_sleep.call_args_list]
        self.assertEqual(actual, [1.5, 3.0, 6.0])

    @mock.patch("docalyzer.openai_client.openai_module.OpenAI")
    def test_summarize_writes_to_file_when_tofile_path_is_provided(
        self, mock_openai: mock.Mock
    ) -> None:
        mock_response = mock.Mock()
        mock_response.output_text = '{"document_title":"Doc","full_summary":"hello"}'
        mock_openai.return_value.responses.create.return_value = mock_response

        client = OpenAIClient(api_key=self.api_key)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"
            result = client.summarize(
                "This is a long text.",
                output_format=OutputEnum.JSON,
                tofile_path=output_path,
            )

            self.assertEqual(result, '{"document_title":"Doc","full_summary":"hello"}')
            self.assertTrue(output_path.exists())
            saved_text = output_path.read_text(encoding="utf-8")
            self.assertIn('  "document_title": "Doc"', saved_text)


if __name__ == "__main__":
    unittest.main()
