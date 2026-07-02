from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "main_shortcut.py"


class MainCLITest(unittest.TestCase):
    def test_cli_help(self) -> None:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

    def test_cli_unknown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "missing.txt"
            result = subprocess.run(
                ["python3", str(SCRIPT), str(missing_file)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("File not found", result.stdout)

    def test_sentences_requires_gemini(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--sentences",
                    "5",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "--sentences requires flag --gemini",
                result.stdout,
            )

    def test_model_requires_gemini(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--model",
                    "high",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "--model requires flag --gemini",
                result.stdout,
            )

    def test_sentences_cannot_be_zero(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--sentences",
                    "0",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "Sentences cannot be less than 1 and more than 250",
                result.stdout,
            )

    def test_sentences_cannot_be_negative(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--sentences",
                    "-5",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "Sentences cannot be less than 1 and more than 250",
                result.stdout,
            )

    def test_sentences_cannot_exceed_limit(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--sentences",
                    "251",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "Sentences cannot be less than 1 and more than 250",
                result.stdout,
            )

    def test_output_requires_gemini(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--output",
                    "md",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "--output requires flag --gemini",
                result.stdout,
            )

    def test_default_output_plain_does_not_require_gemini(self) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8"
        ) as tmpfile:
            tmpfile.write("Sentence one. Sentence two. Sentence three.")
            tmpfile.flush()

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotIn("--output requires flag --gemini", result.stdout)

    def test_tofile_requires_gemini(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--tofile",
                    "summary.md",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("--tofile requires flag --gemini", result.stdout)

    def test_tofile_with_gemini_is_allowed_without_explicit_output(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--tofile",
                    "summary.txt",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotIn("--tofile requires flag --output", result.stdout)
            self.assertNotIn("--tofile requires flag --gemini", result.stdout)

    def test_tofile_with_default_output_does_not_trigger_output_requires_gemini(
        self,
    ) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--tofile",
                    "summary.txt",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("--tofile requires flag --gemini", result.stdout)
            self.assertNotIn("--output requires flag --gemini", result.stdout)

    def test_levels_with_gemini_do_not_raise_type_error(self) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8"
        ) as tmpfile:
            tmpfile.write("Sentence one. Sentence two. Sentence three.")
            tmpfile.flush()

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--desc_level",
                    "2",
                    "--sum_level",
                    "3",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotIn("TypeError", result.stderr)
            self.assertNotIn(
                "unexpected keyword argument 'description_level'", result.stderr
            )
            self.assertNotIn(
                "unexpected keyword argument 'summary_level'", result.stderr
            )

    def test_invalid_output_value(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--output",
                    "invalid",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid", result.stderr.lower())

    def test_gemini_accepts_markdown_output(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--output",
                    "md",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotIn("--output requires flag --gemini", result.stdout)
            self.assertNotIn("invalid choice", result.stderr.lower())

    def test_invalid_model_value(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".md") as tmpfile:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    tmpfile.name,
                    "--gemini",
                    "--model",
                    "invalid",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
