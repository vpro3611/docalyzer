from __future__ import annotations

import json
import re
from pathlib import Path

from docalyzer.outupt_enum import OutputEnum


def normalize_output_content(content: str, output_format: OutputEnum) -> str:
    cleaned_content = content.strip()

    if output_format is not OutputEnum.JSON:
        return cleaned_content

    fenced_match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```", cleaned_content, re.DOTALL
    )
    if fenced_match is not None:
        cleaned_content = fenced_match.group(1).strip()

    try:
        parsed_json = json.loads(cleaned_content)
    except json.JSONDecodeError:
        return cleaned_content

    return json.dumps(parsed_json, indent=2, ensure_ascii=False) + "\n"


def write_output_file(
    content: str,
    tofile_path: Path,
    output_format: OutputEnum,
) -> Path:
    if tofile_path.suffix and tofile_path.suffix != f".{output_format.value}":
        raise ValueError(
            f"Output file extension '{tofile_path.suffix}' does not match requested format '{output_format.value}'"
        )

    if not tofile_path.suffix:
        tofile_path = tofile_path.with_suffix(f".{output_format.value}")

    normalized_content = normalize_output_content(content, output_format)

    tofile_path.parent.mkdir(parents=True, exist_ok=True)
    tofile_path.write_text(normalized_content, encoding="utf-8")
    print(f"Summary saved to: {tofile_path}")
    return tofile_path
