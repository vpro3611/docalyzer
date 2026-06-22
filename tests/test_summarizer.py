import unittest

from docalyzer.summarizer import summarize_text, summarize_long_text, shorten_title


class SummarizerTest(unittest.TestCase):
    def test_summarize_text_short(self) -> None:
        text = "This is sentence one. This is sentence two. This is sentence three."
        summary = summarize_text(text, max_sentences=2)
        self.assertGreaterEqual(summary.count("."), 2)
        self.assertIn("sentence one", summary)

    def test_summarize_long_text_chunks(self) -> None:
        text = "A." * 5000
        summary = summarize_long_text(text, chunk_size=1000, max_sentences=3)
        self.assertIsInstance(summary, str)

    def test_shorten_title(self) -> None:
        self.assertEqual(shorten_title("hello_world-file"), "hello world file")


if __name__ == "__main__":
    unittest.main()
