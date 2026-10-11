"""Gom từ thành các bộ (deck) để người học chọn trong app.

Hai nguồn deck:
1. **Tự sinh theo tần suất/CEFR** — hợp pháp tuyệt đối, vì chỉ dựa trên dữ liệu
   tần suất mở, không sao chép danh sách có bản quyền của ai.
2. **Do bạn tự biên soạn** — thả file .txt vào thư mục `curated/`.
   Dùng cho TOEIC / IELTS, vì các danh sách TOEIC/IELTS trôi nổi trên mạng
   thường là bản biên soạn CÓ BẢN QUYỀN, không được copy vào app thương mại.
   Hãy tự chọn từ, hoặc dùng danh sách có giấy phép rõ ràng.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import Word


@dataclass
class Deck:
    slug: str
    name_vi: str
    description_vi: str
    cefr: str
    headwords: list[str] = field(default_factory=list)


def _by_rank(words: list[Word], start: int, end: int) -> list[str]:
    return [w.headword for w in words if start <= w.rank <= end]


def _by_cefr(words: list[Word], level: str, limit: int | None = None) -> list[str]:
    picked = [w.headword for w in words if w.cefr == level]
    return picked[:limit] if limit else picked


def generated_decks(words: list[Word]) -> list[Deck]:
    """Deck sinh tự động từ tần suất — luôn có sẵn, không cần biên soạn."""
    decks = [
        Deck(
            slug="core-500",
            name_vi="500 từ nền tảng",
            description_vi="Nhóm từ xuất hiện dày đặc nhất trong tiếng Anh. Học xong hiểu được phần lớn câu thông dụng.",
            cefr="A1",
            headwords=_by_rank(words, 1, 500),
        ),
        Deck(
            slug="core-1500",
            name_vi="1500 từ thông dụng",
            description_vi="Mở rộng từ bộ nền tảng, đủ cho giao tiếp hằng ngày.",
            cefr="A2",
            headwords=_by_rank(words, 501, 1500),
        ),
        Deck(
            slug="core-3000",
            name_vi="3000 từ phổ thông",
            description_vi="Vốn từ mục tiêu cho trình độ trung cấp.",
            cefr="B1",
            headwords=_by_rank(words, 1501, 3000),
        ),
    ]

    for level, name, description in [
        ("A1", "Cấp độ A1", "Từ cực phổ biến, người mới bắt đầu."),
        ("A2", "Cấp độ A2", "Từ phổ biến, giao tiếp cơ bản."),
        ("B1", "Cấp độ B1", "Trình độ trung cấp."),
        ("B2", "Cấp độ B2", "Trung cao cấp, đọc báo tiếng Anh."),
        ("C1", "Cấp độ C1", "Nâng cao, học thuật."),
        ("C2", "Cấp độ C2", "Từ hiếm, trình độ gần bản ngữ."),
    ]:
        picked = _by_cefr(words, level)
        if picked:
            decks.append(
                Deck(
                    slug=f"cefr-{level.lower()}",
                    name_vi=name,
                    description_vi=f"{description} Phân loại theo tần suất xuất hiện (xấp xỉ CEFR).",
                    cefr=level,
                    headwords=picked,
                )
            )

    return [deck for deck in decks if deck.headwords]


HEADER_RE = re.compile(r"^#\s*(name|description|cefr)\s*:\s*(.+)$", re.IGNORECASE)


def curated_decks(directory: Path, words: list[Word]) -> list[Deck]:
    """Đọc deck tự biên soạn từ `curated/*.txt`.

    Định dạng file:

        # name: TOEIC 600
        # description: Từ vựng nền cho mục tiêu TOEIC 600
        # cefr: B1
        accomplish
        agenda
        ...

    Từ nào không có trong dataset sẽ bị bỏ qua và báo ra màn hình.
    """
    if not directory.exists():
        return []

    available = {w.headword for w in words}
    decks: list[Deck] = []

    for path in sorted(directory.glob("*.txt")):
        meta = {"name": path.stem, "description": "", "cefr": "B1"}
        headwords: list[str] = []
        missing: list[str] = []

        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            header = HEADER_RE.match(line)
            if header:
                meta[header.group(1).lower()] = header.group(2).strip()
                continue
            if line.startswith("#"):
                continue

            word = line.lower()
            if word in available:
                headwords.append(word)
            else:
                missing.append(word)

        if missing:
            print(f"  ! {path.name}: {len(missing)} từ không có trong dataset "
                  f"(ví dụ: {', '.join(missing[:5])})")

        if headwords:
            decks.append(
                Deck(
                    slug=path.stem.lower().replace(" ", "-"),
                    name_vi=meta["name"],
                    description_vi=meta["description"],
                    cefr=meta["cefr"].upper(),
                    headwords=headwords,
                )
            )

    return decks


def build_all(words: list[Word], curated_dir: Path) -> list[Deck]:
    return generated_decks(words) + curated_decks(curated_dir, words)
