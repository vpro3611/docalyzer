from __future__ import annotations

import os
from pathlib import Path

from google import genai

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


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
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = genai.Client(api_key=api_key)

    @classmethod
    def from_env(
        cls,
        model: str = "gemini-2.5-flash",
        env_path: str | Path | None = None,
    ) -> "GeminiClient":
        _load_dotenv_file(env_path)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        model = os.environ.get("GEMINI_MODEL", model)
        return cls(api_key=api_key, model=model)

    def summarize(self, text: str, max_sentences: int = 5) -> str:
        prompt = (
            "Summarize the following text in a concise way "
            f"using no more than {max_sentences} sentences.\n\n"
            f"Text:\n{text.strip()}"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        if not hasattr(response, "text"):
            raise GeminiAPIError("Unexpected Gemini SDK response: missing text")

        return str(response.text).strip()

