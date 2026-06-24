from __future__ import annotations

import unittest

from docalyzer.gemini_client import DEFAULT_MODEL
from docalyzer.model_enum import MODEL_MAP, ModelEnum


class ModelEnumTest(unittest.TestCase):
    def test_model_enum_values_are_stable_cli_choices(self) -> None:
        self.assertEqual(ModelEnum.LOW.value, "low")
        self.assertEqual(ModelEnum.MID.value, "mid")
        self.assertEqual(ModelEnum.HIGH.value, "high")

    def test_model_map_covers_all_enum_values(self) -> None:
        self.assertEqual(set(MODEL_MAP.keys()), set(ModelEnum))

    def test_mid_effort_maps_to_default_model(self) -> None:
        self.assertEqual(MODEL_MAP[ModelEnum.MID], DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
