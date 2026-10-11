"""Kiểu dữ liệu chung của pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Word:
    headword: str
    rank: int
    zipf: float
    cefr: str

    pos: str | None = None
    pos_vi: str | None = None

    ipa_us: str | None = None
    ipa_uk: str | None = None

    definition_en: str | None = None
    definition_vi: str | None = None
    definition_vi_alt: list[str] = field(default_factory=list)
    vi_source: str | None = None

    example_en: str | None = None
    synonyms: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Đủ điều kiện đưa vào app: phải có cả nghĩa Anh và nghĩa Việt."""
        return bool(self.definition_en and self.definition_vi)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
