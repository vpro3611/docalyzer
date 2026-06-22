from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "main.py"


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


if __name__ == "__main__":
    unittest.main()
