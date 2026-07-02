from __future__ import annotations

from docalyzer.ai_types import AIClient
from docalyzer.gemini_client import DEFAULT_MODEL as GEMINI_DEFAULT_MODEL
from docalyzer.gemini_client import GeminiClient
from docalyzer.model_enum import MODEL_MAP, ModelEnum
from docalyzer.openai_client import DEFAULT_MODEL as OPENAI_DEFAULT_MODEL
from docalyzer.openai_client import OPENAI_MODEL_MAP, OpenAIClient
from docalyzer.provider_enum import ProviderEnum


def resolve_model_name(
    provider: ProviderEnum,
    model_kind: ModelEnum | None = None,
) -> str:
    if provider is ProviderEnum.GEMINI:
        if model_kind is None:
            return GEMINI_DEFAULT_MODEL
        return MODEL_MAP[model_kind]

    if provider is ProviderEnum.OPENAI:
        if model_kind is None:
            return OPENAI_DEFAULT_MODEL
        return OPENAI_MODEL_MAP[model_kind]

    raise ValueError(f"Unsupported provider: {provider}")


def create_ai_client(
    provider: ProviderEnum,
    model_kind: ModelEnum | None = None,
) -> AIClient:
    model_name = resolve_model_name(provider, model_kind)

    if provider is ProviderEnum.GEMINI:
        return GeminiClient.from_env(model=model_name)

    if provider is ProviderEnum.OPENAI:
        return OpenAIClient.from_env(model=model_name)

    raise ValueError(f"Unsupported provider: {provider}")
