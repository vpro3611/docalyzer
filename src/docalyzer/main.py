from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    SRC_ROOT = Path(__file__).resolve().parents[1]
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

from docalyzer.file_loaders import SUPPORTED_EXTENSIONS, FileLoadError, load_file
from docalyzer.model_enum import ModelEnum
from docalyzer.outupt_enum import OutputEnum
from docalyzer.summarizer import shorten_title, summarize_long_text

SENTENCES_MIN: int = 1
SENTENCES_MAX: int = 250

DESCRIPTION_LEVEL_MIN: int = 1
DESCRIPTION_LEVEL_MAX: int = 3

SUMMARY_LEVEL_MIN: int = 1
SUMMARY_LEVEL_MAX: int = 3


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
    parser.add_argument(
        "--tofile",
        type=Path,
        default=None,
        help="Path to the output file, where the summary will be saved.",
    )
    parser.add_argument(
        "--desc_level",
        type=int,
        default=2,
        help="Description level: 1 - brief, 2 - detailed (default), 3 - very detailed (full).",
    )
    parser.add_argument(
        "--sum_level",
        type=int,
        default=2,
        help="Summary level: 1 - brief, 2 - detailed (default), 3 - very detailed (full).",
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
        if args.sentences < SENTENCES_MIN or args.sentences > SENTENCES_MAX:
            print(
                f"Sentences cannot be less than {SENTENCES_MIN} and more than {SENTENCES_MAX}! Current amount: {args.sentences}"
            )
            return 1
        max_sentences = args.sentences

    if args.model is not None and not args.gemini:
        print("--model requires flag --gemini and only works with AI summarizer")
        return 1

    if args.tofile is not None and not args.gemini:
        print("--tofile requires flag --gemini and only works with AI summarizer")
        return 1

    if args.output != OutputEnum.PLAIN and not args.gemini:
        print("--output requires flag --gemini and only works with AI summarizer")
        return 1

    if args.desc_level and not args.gemini:
        print("--desc_level requires flag --gemini and only works with AI summarizer")
        return 1

    if (
        args.desc_level < DESCRIPTION_LEVEL_MIN
        or args.desc_level > DESCRIPTION_LEVEL_MAX
    ):
        print(
            f"Description level must be between {DESCRIPTION_LEVEL_MIN} and {DESCRIPTION_LEVEL_MAX}. "
            f"Got: {args.desc_level}"
        )
        return 1

    if args.sum_level and not args.gemini:
        print("--sum_level requires flag --gemini and only works with AI summarizer")
        return 1

    if args.sum_level < SUMMARY_LEVEL_MIN or args.sum_level > SUMMARY_LEVEL_MAX:
        print(
            f"Summary level must be between {SUMMARY_LEVEL_MIN} and {SUMMARY_LEVEL_MAX}. "
            f"Got: {args.sum_level}"
        )
        return 1

    tofile_path: Path | None = args.tofile if args.tofile is not None else None

    output: OutputEnum = args.output

    model: ModelEnum | None = None

    description_level: int = args.desc_level

    summary_level: int = args.sum_level

    if args.model is None:
        model = ModelEnum.MID
    else:
        model = args.model

    print(f"Target: {path}")

    if args.gemini:
        print(f"Max sentences output: {max_sentences}")
        print(f"Model effort: {model}")
        print(f"Output format: {output}")
        print(
            f"Output file: {tofile_path if tofile_path is not None else 'No output file specified, not saved'}"
        )
        print(
            f"Description level: {description_level} : {'brief' if description_level == 1 else 'detailed' if description_level == 2 else 'full'}"
        )
        print(
            f"Summary level: {summary_level} : {'brief' if summary_level == 1 else 'detailed' if summary_level == 2 else 'full'}"
        )

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
        tofile_path=tofile_path,
        description_level=description_level,
        summary_level=summary_level,
    )

    print("\n=== Summary ===\n")
    print(f"File: {path.name}")
    print(f"Title: {title}\n")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
