from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from docalyzer.outupt_enum import OutputEnum


@dataclass(slots=True)
class SummaryRequest:
    text: str
    max_sentences: int = 5
    output_format: OutputEnum = OutputEnum.PLAIN
    tofile_path: Path | None = None
    description_level: int = 2
    summary_level: int = 2


@runtime_checkable
class AIClient(Protocol):
    def summarize_request(self, request: SummaryRequest) -> str: ...
