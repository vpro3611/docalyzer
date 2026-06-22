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
            path = Path(tmpdir) / "hello.json"
            path.write_text("{\"key\": \"value\"}", encoding="utf-8")
            with self.assertRaises(FileLoadError):
                load_file(path)


if __name__ == "__main__":
    unittest.main()
