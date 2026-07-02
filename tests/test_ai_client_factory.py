from __future__ import annotations

import unittest
from unittest import mock

from docalyzer.ai_client_factory import create_ai_client, resolve_model_name
from docalyzer.gemini_client import DEFAULT_MODEL as GEMINI_DEFAULT_MODEL
from docalyzer.model_enum import MODEL_MAP, ModelEnum
from docalyzer.openai_client import DEFAULT_MODEL as OPENAI_DEFAULT_MODEL
from docalyzer.openai_client import OPENAI_MODEL_MAP
from docalyzer.provider_enum import ProviderEnum


class AIClientFactoryTest(unittest.TestCase):
    def test_resolve_model_name_uses_gemini_default(self) -> None:
        self.assertEqual(
            resolve_model_name(ProviderEnum.GEMINI),
            GEMINI_DEFAULT_MODEL,
        )

    def test_resolve_model_name_uses_openai_default(self) -> None:
        self.assertEqual(
            resolve_model_name(ProviderEnum.OPENAI),
            OPENAI_DEFAULT_MODEL,
        )

    def test_resolve_model_name_uses_selected_gemini_model_kind(self) -> None:
        self.assertEqual(
            resolve_model_name(ProviderEnum.GEMINI, ModelEnum.HIGH),
            MODEL_MAP[ModelEnum.HIGH],
        )

    def test_resolve_model_name_uses_selected_openai_model_kind(self) -> None:
        self.assertEqual(
            resolve_model_name(ProviderEnum.OPENAI, ModelEnum.LOW),
            OPENAI_MODEL_MAP[ModelEnum.LOW],
        )

    @mock.patch("docalyzer.ai_client_factory.GeminiClient.from_env")
    def test_create_ai_client_builds_gemini_client(
        self, mock_from_env: mock.Mock
    ) -> None:
        client = object()
        mock_from_env.return_value = client

        result = create_ai_client(ProviderEnum.GEMINI, model_kind=ModelEnum.MID)

        self.assertIs(result, client)
        mock_from_env.assert_called_once_with(model=MODEL_MAP[ModelEnum.MID])

    @mock.patch("docalyzer.ai_client_factory.OpenAIClient.from_env")
    def test_create_ai_client_builds_openai_client(
        self, mock_from_env: mock.Mock
    ) -> None:
        client = object()
        mock_from_env.return_value = client

        result = create_ai_client(ProviderEnum.OPENAI, model_kind=ModelEnum.LOW)

        self.assertIs(result, client)
        mock_from_env.assert_called_once_with(model=OPENAI_MODEL_MAP[ModelEnum.LOW])


if __name__ == "__main__":
    unittest.main()
