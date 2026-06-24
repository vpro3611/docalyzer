from __future__ import annotations

import argparse
from pathlib import Path

from docalyzer.file_loaders import FileLoadError, SUPPORTED_EXTENSIONS, load_file
from docalyzer.summarizer import shorten_title, summarize_long_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI summarizer MVP for documents and code files."
    )
    parser.add_argument(
        "path",
        type=Path,
        help=(
            "Path to the file to summarize. Supported extensions: "
            f"{', '.join(SUPPORTED_EXTENSIONS)}"
        ),
    )
    parser.add_argument(
        "--sentences",
        type=int,
        default=5,
        help="Maximum number of sentences in the summary.",
    )
    parser.add_argument(
        "--gemini",
        action="store_true",
        help="Use Gemini LLM API for summarization.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    path = args.path

    if not path.exists():
        print(f"File not found: {path}")
        return 1

    try:
        raw_text = load_file(path)
    except FileLoadError as error:
        print(f"Error: {error}")
        return 1
    except Exception as error:
        print(f"Unexpected error: {error}")
        return 1

    title = shorten_title(path.stem)
    summary = summarize_long_text(
        raw_text,
        max_sentences=args.sentences,
        use_gemini=args.gemini,
    )

    print("\n=== Summary ===\n")
    print(f"File: {path.name}")
    print(f"Title: {title}\n")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
