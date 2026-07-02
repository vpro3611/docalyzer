from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from docalyzer.output_writer import normalize_output_content, write_output_file
from docalyzer.outupt_enum import OutputEnum
from docalyzer.prompt_builder import build_summary_prompt
from docalyzer.provider_enum import ProviderEnum


class PromptBuilderTest(unittest.TestCase):
    def test_build_summary_prompt_defaults_invalid_levels_to_detailed_prompts(
        self,
    ) -> None:
        prompt = build_summary_prompt(
            "Some text.",
            OutputEnum.PLAIN,
            max_sentences=5,
            description_level=99,
            summary_level=99,
        )

        self.assertIn("Provide a detailed description of the given text.", prompt)
        self.assertIn(
            "The summary should be detailed, but still fit into the sentences cap.",
            prompt,
        )

    def test_build_summary_prompt_uses_unknown_output_fallback(self) -> None:
        prompt = build_summary_prompt("Some text.", "yaml", max_sentences=4)

        self.assertIn("professional plain text format", prompt)
        self.assertIn("If the requested format is unknown", prompt)
        self.assertIn("Text:\n\nSome text.", prompt)

    def test_build_summary_prompt_uses_json_rules(self) -> None:
        prompt = build_summary_prompt(
            "Some text.",
            OutputEnum.JSON,
            max_sentences=6,
            description_level=3,
            summary_level=1,
        )

        self.assertIn("Return only valid JSON", prompt)
        self.assertIn("Include full_summary with a maximum of 6 sentences", prompt)
        self.assertIn(
            "Provide an in-depth and very detailed description of the given text.",
            prompt,
        )
        self.assertIn(
            "The summary should be concise, but still fit into the sentences cap.",
            prompt,
        )


class OutputWriterTest(unittest.TestCase):
    def test_normalize_output_content_strips_non_json_content(self) -> None:
        normalized = normalize_output_content("  hello world  ", OutputEnum.PLAIN)

        self.assertEqual(normalized, "hello world")

    def test_normalize_output_content_pretty_prints_fenced_json(self) -> None:
        normalized = normalize_output_content(
            '```json\n{"document_title":"Doc","full_summary":"hello"}\n```',
            OutputEnum.JSON,
        )

        self.assertIn('  "document_title": "Doc"', normalized)
        self.assertIn('  "full_summary": "hello"', normalized)
        self.assertTrue(normalized.endswith("\n"))

    def test_normalize_output_content_keeps_invalid_json_as_cleaned_text(self) -> None:
        normalized = normalize_output_content(
            '  {"document_title": invalid json}  ',
            OutputEnum.JSON,
        )

        self.assertEqual(normalized, '{"document_title": invalid json}')

    def test_write_output_file_adds_missing_suffix_and_returns_final_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "summary"

            saved_path = write_output_file(
                "Saved summary",
                output_path,
                OutputEnum.MARKDOWN,
            )

            self.assertEqual(saved_path, output_path.with_suffix(".md"))
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_text(encoding="utf-8"), "Saved summary")

    def test_write_output_file_rejects_mismatched_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"

            with self.assertRaises(ValueError) as ctx:
                write_output_file("Saved summary", output_path, OutputEnum.PLAIN)

            self.assertIn("does not match requested format", str(ctx.exception))


class ProviderEnumTest(unittest.TestCase):
    def test_display_name_for_gemini(self) -> None:
        self.assertEqual(ProviderEnum.GEMINI.display_name, "Gemini")

    def test_display_name_for_openai(self) -> None:
        self.assertEqual(ProviderEnum.OPENAI.display_name, "OpenAI")


if __name__ == "__main__":
    unittest.main()
