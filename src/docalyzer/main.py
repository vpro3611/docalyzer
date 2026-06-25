from __future__ import annotations

import argparse
from pathlib import Path

from docalyzer.file_loaders import SUPPORTED_EXTENSIONS, FileLoadError, load_file
from docalyzer.model_enum import ModelEnum
from docalyzer.outupt_enum import OutputEnum
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
        default=None,
        help="Maximum number of sentences in the summary.",
    )
    parser.add_argument(
        "--gemini",
        action="store_true",
        help="Use Gemini LLM API for summarization.",
    )
    parser.add_argument(
        "--model",
        type=ModelEnum,
        default=None,
        help="Define model which will be used for summary. Available: low, mid, high",
    )
    parser.add_argument(
        "--output",
        type=OutputEnum,
        default=OutputEnum.PLAIN,
        help="Output format for the summary. Available: txt, md, json",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    path = args.path
    max_sentences: int = 5

    if not path.exists():
        print(f"File not found: {path}")
        return 1

    if args.sentences is not None and not args.gemini:
        print("--sentences requires flag --gemini and only works with AI summarizer")
        return 1

    if args.sentences is not None and args.gemini:
        if args.sentences < 1 or args.sentences > 250:
            print(
                f"Sentences cannot be less than 1 and more than 250! Current amount: {args.sentences}"
            )
            return 1
        max_sentences = args.sentences

    if args.model is not None and not args.gemini:
        print("--model requires flag --gemini and only works with AI summarizer")
        return 1

    if args.output is not None and not args.gemini:
        print("--output requires flag --gemini and only works with AI summarizer")
        return 1

    output: OutputEnum = OutputEnum.PLAIN if args.output is None else args.output

    model: ModelEnum | None = None

    if args.model is None:
        model = ModelEnum.MID
    else:
        model = args.model

    print(f"Target: {path}")

    if args.gemini:
        print(f"Max sentences output: {max_sentences}")
        print(f"Model effort: {model}")
        print(f"Output format: {output}")

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
        model_kind=model,
        max_sentences=max_sentences,
        use_gemini=args.gemini,
        output_format=output,
    )

    print("\n=== Summary ===\n")
    print(f"File: {path.name}")
    print(f"Title: {title}\n")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
