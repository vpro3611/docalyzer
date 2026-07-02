from __future__ import annotations

import re
from pathlib import Path

from docalyzer.ai_client_factory import create_ai_client
from docalyzer.ai_errors import AIConfigurationError, AISummarizationError
from docalyzer.ai_executor import AIExecutor
from docalyzer.ai_types import SummaryRequest
from docalyzer.model_enum import ModelEnum
from docalyzer.outupt_enum import OutputEnum
from docalyzer.provider_enum import ProviderEnum


def summarize_text(text: str, max_sentences: int = 5) -> str:
    if not text or not text.strip():
        return "No readable content found."

    cleaned = _normalize_whitespace(text)
    sentences = _split_sentences(cleaned)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    return " ".join(sentences[:max_sentences])


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def summarize_long_text(
    text: str,
    model_kind: ModelEnum | None = None,
    chunk_size: int = 2000,
    max_sentences: int = 5,
    use_gemini: bool = False,
    provider: ProviderEnum | None = None,
    output_format: OutputEnum = OutputEnum.PLAIN,
    tofile_path: Path | None = None,
    description_level: int = 2,
    summary_level: int = 2,
) -> str:
    if provider is None and use_gemini:
        provider = ProviderEnum.GEMINI

    if provider is not None:
        if use_gemini and provider is not ProviderEnum.GEMINI:
            raise ValueError("use_gemini cannot be combined with a non-Gemini provider")

        request = SummaryRequest(
            text=text,
            max_sentences=max_sentences,
            output_format=output_format,
            tofile_path=tofile_path,
            description_level=description_level,
            summary_level=summary_level,
        )

        try:
            client = create_ai_client(provider, model_kind=model_kind)
            return AIExecutor(client).summarize(request)
        except ImportError as error:
            return f"{provider.display_name} summarization failed: {error}"
        except AISummarizationError as error:
            return f"{provider.display_name} summarization failed: {error}"
        except AIConfigurationError as error:
            return f"{provider.display_name} configuration error: {error}"

    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    chunk_summaries = [summarize_text(chunk, max_sentences=2) for chunk in chunks]
    return "\n\n".join(chunk_summaries)


def shorten_title(path_name: str) -> str:
    return path_name.replace("_", " ").replace("-", " ")
