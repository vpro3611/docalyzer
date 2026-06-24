from __future__ import annotations

import re
from docalyzer.gemini_client import GeminiAPIError, GeminiClient


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
    chunk_size: int = 2000,
    max_sentences: int = 5,
    use_gemini: bool = False,
) -> str:
    if use_gemini:
        try:
            client = GeminiClient.from_env()
            return client.summarize(text, max_sentences=max_sentences)
        except GeminiAPIError as error:
            return f"Gemini summarization failed: {error}"
        except ValueError as error:
            return f"Gemini configuration error: {error}"

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    chunk_summaries = [
        summarize_text(chunk, max_sentences=2) for chunk in chunks
    ]
    return "\n\n".join(chunk_summaries)


def shorten_title(path_name: str) -> str:
    return path_name.replace("_", " ").replace("-", " ")
