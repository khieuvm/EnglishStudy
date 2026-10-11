"""Chọn danh sách từ ứng viên + gán cấp độ CEFR dựa trên tần suất.

Nguồn: thư viện `wordfreq` (MIT) — tổng hợp tần suất từ nhiều corpus mở.
Lý do KHÔNG dùng Oxford 3000/5000: Oxford không công bố license cho phép
tải về / dùng thương mại (xem ATTRIBUTIONS.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from wordfreq import top_n_list, zipf_frequency

WORD_RE = re.compile(r"^[a-z]+$")

# Từ chức năng: cần cho ngữ pháp nhưng vô nghĩa khi học flashcard từ vựng.
FUNCTION_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "that", "this",
    "these", "those", "there", "here", "is", "are", "was", "were", "be", "been",
    "being", "am", "do", "does", "did", "done", "have", "has", "had", "having",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "mine", "yours", "hers", "ours",
    "theirs", "myself", "yourself", "himself", "herself", "itself", "ourselves",
    "themselves", "of", "in", "on", "at", "to", "for", "with", "by", "from",
    "about", "into", "onto", "over", "under", "between", "through", "during",
    "before", "after", "above", "below", "up", "down", "out", "off", "again",
    "not", "no", "nor", "so", "too", "very", "just", "now", "also", "as",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "s", "t", "don", "ll", "re", "ve", "m", "d",
}

# Ngưỡng Zipf → CEFR. Zipf 7 ≈ cực phổ biến ("the"), Zipf 3 ≈ hiếm.
# Đây là xấp xỉ theo tần suất, KHÔNG phải CEFR chính thức của Hội đồng châu Âu.
CEFR_THRESHOLDS: list[tuple[float, str]] = [
    (5.60, "A1"),
    (5.00, "A2"),
    (4.50, "B1"),
    (4.00, "B2"),
    (3.50, "C1"),
    (0.00, "C2"),
]


def cefr_for_zipf(zipf: float) -> str:
    for threshold, level in CEFR_THRESHOLDS:
        if zipf >= threshold:
            return level
    return "C2"


@dataclass(frozen=True)
class Candidate:
    headword: str
    rank: int
    zipf: float
    cefr: str


def candidates(
    limit: int,
    *,
    min_length: int = 3,
    pool_multiplier: int = 4,
    lemmatizer: Callable[[str], str] | None = None,
) -> list[Candidate]:
    """Lấy `limit` từ phổ biến nhất sau khi lọc nhiễu và quy về dạng gốc.

    `pool_multiplier`: lấy dư rồi lọc, vì nhiều mục trong top list là từ chức
    năng, viết tắt, dạng biến thể trùng lặp, hoặc không phải từ thuần chữ cái.
    """
    pool = top_n_list("en", limit * pool_multiplier)

    out: list[Candidate] = []
    seen: set[str] = set()

    for word in pool:
        if len(out) >= limit:
            break
        word = word.lower()
        if len(word) < min_length or not WORD_RE.match(word):
            continue
        if word in FUNCTION_WORDS:
            continue

        headword = lemmatizer(word) if lemmatizer else word

        # Dạng gốc có thể rơi vào danh sách từ chức năng (ví dụ "does" -> "do").
        if headword in seen or headword in FUNCTION_WORDS:
            continue
        if len(headword) < min_length or not WORD_RE.match(headword):
            continue

        seen.add(headword)
        zipf = zipf_frequency(headword, "en")
        out.append(
            Candidate(
                headword=headword,
                rank=len(out) + 1,
                zipf=zipf,
                cefr=cefr_for_zipf(zipf),
            )
        )

    return out
