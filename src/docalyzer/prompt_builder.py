from __future__ import annotations

from docalyzer.description_level import DESCRIPTION_LEVEL_TO_PROMPT
from docalyzer.outupt_enum import OutputEnum
from docalyzer.summary_level import SUMMARY_LEVEL_TO_PROMPT


def build_summary_prompt(
    text: str,
    output_format: OutputEnum | str,
    max_sentences: int,
    description_level: int = 2,
    summary_level: int = 2,
) -> str:
    detail_instruction = DESCRIPTION_LEVEL_TO_PROMPT.get(
        description_level,
        DESCRIPTION_LEVEL_TO_PROMPT[2],
    )
    summary_instruction = SUMMARY_LEVEL_TO_PROMPT.get(
        summary_level,
        SUMMARY_LEVEL_TO_PROMPT[2],
    )

    match output_format:
        case OutputEnum.PLAIN:
            return (
                "Summarize the following text in professional plain text format.\n\n"
                "Make the output clear, polished, and easy to read.\n\n"
                "Use short paragraphs or simple bullet-style lines where appropriate, but do not use Markdown syntax or JSON.\n\n"
                f"Include a summary using no more than {max_sentences} sentences.\n\n"
                f"{detail_instruction}\n\n"
                f"{summary_instruction}.\n\n"
                "Put a double newline after each line or section for readable plain text spacing.\n\n"
                f"The output format must be {output_format.value} (plain text).\n\n"
                f"Text:\n\n{text.strip()}"
            )
        case OutputEnum.MARKDOWN:
            return (
                "Summarize the following text in professional Markdown format.\n\n"
                "Make the output clear, polished, and easy to scan.\n\n"
                "Use proper Markdown headers and bullet points where appropriate.\n\n"
                f"Include a summary section using no more than {max_sentences} sentences.\n\n"
                f"{detail_instruction}\n\n"
                f"{summary_instruction}.\n\n"
                "Put a double newline after each line or section for readable Markdown spacing.\n\n"
                f"The output format must be {output_format.value} (Markdown).\n\n"
                f"Text:\n\n{text.strip()}"
            )
        case OutputEnum.JSON:
            return (
                "Summarize the following text in JSON format.\n\n"
                "Return only valid JSON with no surrounding commentary, no markdown fences, and no additional text.\n\n"
                f"The output format must be {output_format.value} (JSON).\n\n"
                "JSON rules:\n\n"
                "1) Use snake_case for all keys.\n\n"
                "2) Include document_title if applicable.\n\n"
                "3) Include short_description with exactly 3 sentences.\n\n"
                "4) Include short_summary with 2 to 3 sentences.\n\n"
                f"5) Include full_summary with a maximum of {max_sentences} sentences, as provided by the user.\n\n"
                f"6) {detail_instruction}\n\n"
                f"7) {summary_instruction}.\n\n"
                "8) Keep values concise, factual, and based only on the provided text.\n\n"
                "9) If a title is not available, use an empty string for document_title.\n\n"
                "Use this JSON structure:\n\n"
                "{\n"
                '  "document_title": "",\n'
                '  "short_description": "",\n'
                '  "short_summary": "",\n'
                '  "full_summary": ""\n'
                "}\n\n"
                f"Text:\n\n{text.strip()}"
            )
        case _:
            return (
                "Summarize the following text in professional plain text format.\n\n"
                "Make the output clear, polished, and easy to read.\n\n"
                "Use short paragraphs or simple bullet-style lines where appropriate, but do not use Markdown syntax or JSON.\n\n"
                f"Include a summary using no more than {max_sentences} sentences.\n\n"
                f"{detail_instruction}\n\n"
                f"{summary_instruction}.\n\n"
                "Put a double newline after each line or section for readable plain text spacing.\n\n"
                "If the requested format is unknown, default to clean plain text output.\n\n"
                f"Text:\n\n{text.strip()}"
            )
