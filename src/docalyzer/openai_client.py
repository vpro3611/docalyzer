from __future__ import annotations

import logging
import os
import time
import types
from pathlib import Path
from typing import Any

from docalyzer.ai_errors import AIConfigurationError, AISummarizationError
from docalyzer.ai_types import SummaryRequest
from docalyzer.model_enum import ModelEnum
from docalyzer.output_writer import normalize_output_content, write_output_file
from docalyzer.outupt_enum import OutputEnum
from docalyzer.prompt_builder import build_summary_prompt

DEFAULT_MODEL: str = "gpt-4.1"

OPENAI_MODEL_MAP = {
    ModelEnum.LOW: "gpt-4.1-mini",
    ModelEnum.MID: DEFAULT_MODEL,
    ModelEnum.HIGH: "gpt-5.2",
}

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

logger = logging.getLogger(__name__)

openai_module = types.SimpleNamespace(
    OpenAI=None,
    RateLimitError=Exception,
    APITimeoutError=Exception,
    APIConnectionError=Exception,
    APIStatusError=Exception,
    APIError=Exception,
    _is_placeholder=True,
)


def _import_openai() -> Any:
    global openai_module

    if (
        getattr(openai_module, "_is_placeholder", False)
        and openai_module.OpenAI is not None
    ):
        return openai_module

    try:
        import openai as imported_openai
    except ImportError as exc:
        if (
            getattr(openai_module, "_is_placeholder", False)
            and openai_module.OpenAI is not None
        ):
            return openai_module
        raise ImportError(
            "openai is required for OpenAI summarization. "
            "Install it with 'pip install openai' or use a different provider."
        ) from exc

    openai_module = imported_openai
    return openai_module


class OpenAIAPIError(AISummarizationError):
    pass


def _load_dotenv_file(env_path: Path | str | None = None) -> None:
    if load_dotenv is not None:
        load_dotenv(dotenv_path=env_path, override=False)
        return

    env_path = Path(env_path or ".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: int = 30,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        openai_sdk = _import_openai()
        self.client = openai_sdk.OpenAI(api_key=api_key, timeout=timeout)
        self.openai_module = openai_sdk
        logger.debug(
            f"Initialized OpenAIClient with model={model}, max_retries={max_retries}"
        )
        print(f"Model being used: {model}")

    @classmethod
    def from_env(
        cls,
        model: str | None = None,
        env_path: str | Path | None = None,
        max_retries: int = 3,
    ) -> "OpenAIClient":
        _load_dotenv_file(env_path)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise AIConfigurationError("OPENAI_API_KEY is not set in the environment")
        model = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", max_retries))
        logger.debug(f"Loaded OpenAI config from environment: model={model}")
        return cls(api_key=api_key, model=model, max_retries=max_retries)

    def summarize_request(self, request: SummaryRequest) -> str:
        prompt = self._format_request(
            request.text,
            request.output_format,
            request.max_sentences,
            request.description_level,
            request.summary_level,
        )
        content = self._generate_content_with_retry(prompt)
        if request.tofile_path is not None:
            self._write_to_file(content, request.tofile_path, request.output_format)
        return content

    def summarize(
        self,
        text: str,
        max_sentences: int = 5,
        output_format: OutputEnum = OutputEnum.PLAIN,
        tofile_path: Path | None = None,
        description_level: int = 2,
        summary_level: int = 2,
    ) -> str:
        return self.summarize_request(
            SummaryRequest(
                text=text,
                max_sentences=max_sentences,
                output_format=output_format,
                tofile_path=tofile_path,
                description_level=description_level,
                summary_level=summary_level,
            )
        )

    def _write_to_file(
        self, content: str, tofile_path: Path, output_format: OutputEnum
    ) -> None:
        write_output_file(content, tofile_path, output_format)

    def _normalize_output_content(self, content: str, output_format: OutputEnum) -> str:
        return normalize_output_content(content, output_format)

    def _format_request(
        self,
        text: str,
        output_format: OutputEnum | str,
        max_sentences: int,
        description_level: int = 2,
        summary_level: int = 2,
    ) -> str:
        return build_summary_prompt(
            text,
            output_format,
            max_sentences,
            description_level,
            summary_level,
        )

    def _generate_content_with_retry(self, prompt: str) -> str:
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling OpenAI API (attempt {attempt + 1}/{self.max_retries})"
                )
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                )
                text = self._extract_text(response)
                if not text:
                    raise OpenAIAPIError("OpenAI API returned empty text")
                logger.debug(f"OpenAI API call successful on attempt {attempt + 1}")
                return text
            except OpenAIAPIError:
                raise
            except self.openai_module.RateLimitError as error:
                last_error = error
                logger.warning(
                    f"OpenAI rate limit error on attempt {attempt + 1}: {error}"
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)
            except self.openai_module.APITimeoutError as error:
                last_error = error
                logger.warning(f"OpenAI timeout on attempt {attempt + 1}: {error}")
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)
            except self.openai_module.APIConnectionError as error:
                last_error = error
                logger.warning(
                    f"OpenAI connection error on attempt {attempt + 1}: {error}"
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)
            except self.openai_module.APIStatusError as error:
                status_code = getattr(error, "status_code", None)
                if (
                    status_code is not None
                    and int(status_code) < 500
                    and int(status_code) != 429
                ):
                    raise OpenAIAPIError(str(error)) from error
                last_error = error
                logger.warning(
                    f"OpenAI API status error on attempt {attempt + 1}: {error}"
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)
            except self.openai_module.APIError as error:
                last_error = error
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {error}")
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)
            except Exception as error:
                last_error = error
                logger.error(f"Unexpected error on attempt {attempt + 1}: {error}")
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

        raise OpenAIAPIError(
            f"OpenAI API failed after {self.max_retries} retries: {last_error}"
        )

    def _extract_text(self, response: object) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text is not None:
            return str(output_text).strip()

        choices = getattr(response, "choices", None)
        if choices:
            first_choice = choices[0]
            text = getattr(first_choice, "text", None)
            if text is not None:
                return str(text).strip()

            message = getattr(first_choice, "message", None)
            if message is not None:
                content = getattr(message, "content", None)
                if isinstance(content, str):
                    return content.strip()

        raise OpenAIAPIError("OpenAI API returned response without extractable text")

    def _sleep_with_backoff(self, attempt: int) -> None:
        delay = self.initial_retry_delay * (2**attempt)
        logger.debug(f"Backing off for {delay:.1f} seconds before retry")
        time.sleep(delay)
