from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from docalyzer.file_loaders import SUPPORTED_EXTENSIONS, FileLoadError, load_file


class FileLoadersTest(unittest.TestCase):
    def test_supported_extensions_contains_all(self) -> None:
        self.assertIn(".txt", SUPPORTED_EXTENSIONS)
        self.assertIn(".pdf", SUPPORTED_EXTENSIONS)
        self.assertIn(".docx", SUPPORTED_EXTENSIONS)
        self.assertIn(".ipynb", SUPPORTED_EXTENSIONS)

    def test_load_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "hello.txt"
            path.write_text("Hello world!\nThis is a test.", encoding="utf-8")
            result = load_file(path)
            self.assertIn("Hello world", result)

    def test_load_unsupported_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "hello.unsupported"
            path.write_text("some content", encoding="utf-8")
            with self.assertRaises(FileLoadError):
                load_file(path)

    def test_load_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.txt"
            with self.assertRaises(FileNotFoundError):
                load_file(path)

    def test_load_json_file_pretty_prints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            path.write_text('{"name":"Doc","items":[1,2]}', encoding="utf-8")

            result = load_file(path)

            self.assertIn('"name": "Doc"', result)
            self.assertIn('"items": [', result)

    def test_load_xml_file_pretty_prints_valid_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.xml"
            path.write_text("<root><child id='1'>value</child></root>", encoding="utf-8")

            result = load_file(path)

            self.assertIn("<root>", result)
            self.assertIn('<child id="1">', result)
            self.assertIn("value", result)

    def test_load_xml_file_returns_raw_text_for_invalid_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.xml"
            raw_text = "<root><child></root>"
            path.write_text(raw_text, encoding="utf-8")

            result = load_file(path)

            self.assertEqual(result, raw_text)

    def test_load_csv_file_limits_to_first_twenty_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.csv"
            rows = [f"row{index},value{index}" for index in range(25)]
            path.write_text("\n".join(rows), encoding="utf-8")

            result = load_file(path)

            self.assertIn("row0, value0", result)
            self.assertIn("row19, value19", result)
            self.assertNotIn("row20, value20", result)

    def test_load_ipynb_file_extracts_markdown_and_code_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "notebook.ipynb"
            path.write_text(
                """
{
  "cells": [
    {"cell_type": "markdown", "source": ["# Title\\n", "Intro text"]},
    {"cell_type": "code", "source": ["print('hello')\\n"]},
    {"cell_type": "markdown", "source": ["   "]}
  ]
}
""".strip(),
                encoding="utf-8",
            )

            result = load_file(path)

            self.assertIn("# Title", result)
            self.assertIn("Intro text", result)
            self.assertIn("# code cell", result)
            self.assertIn("print('hello')", result)


if __name__ == "__main__":
    unittest.main()
