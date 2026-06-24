from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

logger = logging.getLogger(__name__)


class GeminiAPIError(RuntimeError):
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


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout: int = 30,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.client = genai.Client(api_key=api_key)
        logger.debug(
            "Initialized GeminiClient with model=%s, max_retries=%d",
            model,
            max_retries,
        )

    @classmethod
    def from_env(
        cls,
        model: str = "gemini-2.5-flash",
        env_path: str | Path | None = None,
        max_retries: int = 3,
    ) -> "GeminiClient":
        _load_dotenv_file(env_path)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        model = os.environ.get("GEMINI_MODEL", model)
        max_retries = int(os.environ.get("GEMINI_MAX_RETRIES", max_retries))
        logger.debug(f"Loaded Gemini config from environment: model={model}")
        return cls(api_key=api_key, model=model, max_retries=max_retries)

    def summarize(self, text: str, max_sentences: int = 5) -> str:
        prompt = (
            "Summarize the following text in a concise way "
            f"using no more than {max_sentences} sentences.\n\n"
            f"Text:\n{text.strip()}"
        )

        return self._generate_content_with_retry(prompt)

    def _generate_content_with_retry(self, prompt: str) -> str:
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Calling Gemini API (attempt %d/%d)",
                    attempt + 1,
                    self.max_retries,
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )

                if not hasattr(response, "text"):
                    raise GeminiAPIError(
                        "Gemini API returned response without text field"
                    )

                text = str(response.text).strip()
                if not text:
                    raise GeminiAPIError("Gemini API returned empty text")

                logger.debug(
                    "Gemini API call successful on attempt %d",
                    attempt + 1,
                )
                return text

            except GeminiAPIError:
                # Don't retry on validation errors
                raise

            except genai_errors.ClientError as error:
                last_error = error
                logger.warning(
                    "Gemini client error on attempt %d: %s",
                    attempt + 1,
                    error,
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

            except genai_errors.ServerError as error:
                last_error = error
                logger.warning(
                    "Gemini server error on attempt %d: %s",
                    attempt + 1,
                    error,
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

            except genai_errors.APIError as error:
                last_error = error
                logger.error(
                    "Gemini API error on attempt %d: %s",
                    attempt + 1,
                    error,
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

            except Exception as error:
                last_error = error
                logger.error(
                    "Unexpected error on attempt %d: %s",
                    attempt + 1,
                    error,
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

        raise GeminiAPIError(
            f"Gemini API failed after {self.max_retries} retries: {last_error}"
        )

    def _sleep_with_backoff(self, attempt: int) -> None:
        delay = self.initial_retry_delay * (2 ** attempt)
        logger.debug(f"Backing off for {delay:.1f} seconds before retry")
        time.sleep(delay)