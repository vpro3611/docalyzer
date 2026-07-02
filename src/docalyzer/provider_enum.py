from __future__ import annotations

from enum import StrEnum


class ProviderEnum(StrEnum):
    GEMINI = "gemini"
    OPENAI = "openai"

    @property
    def display_name(self) -> str:
        if self is ProviderEnum.OPENAI:
            return "OpenAI"
        return "Gemini"
