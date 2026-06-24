from __future__ import annotations

import logging
import os
import time
import types
from pathlib import Path

DEFAULT_MODEL: str = "gemini-2.5-flash"

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

logger = logging.getLogger(__name__)

genai = types.SimpleNamespace(Client=None, _is_placeholder=True)
genai_errors = types.SimpleNamespace(
    ClientError=Exception,
    ServerError=Exception,
    APIError=Exception,
    _is_placeholder=True,
)


def _import_genai() -> tuple[object, object]:
    global genai, genai_errors

    if getattr(genai, "_is_placeholder", False) and genai.Client is not None:
        return genai, genai_errors

    try:
        from google import genai as imported_genai
        from google.genai import errors as imported_genai_errors
    except ImportError as exc:
        if getattr(genai, "_is_placeholder", False) and genai.Client is not None:
            return genai, genai_errors
        raise ImportError(
            "google-genai is required for Gemini summarization. "
            "Install it with 'pip install google-genai' or remove --gemini."
        ) from exc

    genai = imported_genai
    genai_errors = imported_genai_errors
    return genai, genai_errors


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
        genai_module, genai_errors_module = _import_genai()
        self.client = genai_module.Client(api_key=api_key)
        self.genai_errors = genai_errors_module
        logger.debug(
            f"Initialized GeminiClient with model={model}, max_retries={max_retries}"
        )
        print(f"Model being used: {model}")

    @classmethod
    def from_env(
        cls,
        model: str | None = None,
        env_path: str | Path | None = None,
        max_retries: int = 3,
    ) -> "GeminiClient":
        _load_dotenv_file(env_path)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
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
                    f"Calling Gemini API (attempt {attempt + 1}/{self.max_retries})"
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

                logger.debug(f"Gemini API call successful on attempt {attempt + 1}")
                return text

            except GeminiAPIError:
                # Don't retry on validation errors
                raise

            except self.genai_errors.ClientError as error:
                last_error = error
                logger.warning(
                    f"Gemini client error on attempt {attempt + 1}: {error}"
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

            except self.genai_errors.ServerError as error:
                last_error = error
                logger.warning(
                    f"Gemini server error on attempt {attempt + 1}: {error}"
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

            except self.genai_errors.APIError as error:
                last_error = error
                logger.error(
                    f"Gemini API error on attempt {attempt + 1}: {error}",
                )
                if attempt < self.max_retries - 1:
                    self._sleep_with_backoff(attempt)

            except Exception as error:
                last_error = error
                logger.error(
                    f"Unexpected error on attempt {attempt + 1}: {error}",
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

