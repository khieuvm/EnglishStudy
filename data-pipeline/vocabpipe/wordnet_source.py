"""Lấy định nghĩa tiếng Anh, loại từ, ví dụ, từ đồng nghĩa từ WordNet.

WordNet (Princeton) cho phép dùng thương mại miễn phí, chỉ cần giữ copyright
notice — đây là lý do nó được chọn làm xương sống của dataset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from nltk.corpus import wordnet as wn

# WordNet dùng ký hiệu riêng; đổi sang nhãn hiển thị cho người học.
POS_LABEL = {
    "n": "noun",
    "v": "verb",
    "a": "adj",
    "s": "adj",   # adjective satellite
    "r": "adv",
}

POS_LABEL_VI = {
    "noun": "danh từ",
    "verb": "động từ",
    "adj": "tính từ",
    "adv": "trạng từ",
}


@dataclass
class WordNetSense:
    pos: str
    definition_en: str
    example_en: str | None
    synonyms: list[str] = field(default_factory=list)
    frequency: int = 0


def ensure_corpus() -> None:
    """Tải WordNet nếu máy chưa có. Gọi một lần lúc khởi động pipeline."""
    try:
        wn.synsets("test")
    except LookupError:
        import nltk

        nltk.download("wordnet", quiet=True)
        wn.synsets("test")


# Nếu dạng gốc hiếm hơn dạng biến thể quá nhiều thì giữ nguyên dạng biến thể
# ("data" phổ biến hơn hẳn "datum" nên không đổi thành "datum").
LEMMA_ZIPF_MARGIN = 0.4


def _morphy_candidates(word: str) -> set[str]:
    """Mọi dạng gốc khả dĩ của `word`, xét qua cả 4 loại từ.

    `wn.morphy()` công khai chỉ trả về MỘT kết quả và ưu tiên danh từ, nên
    "years" vẫn ra "years" (vì WordNet có lemma "years" nghĩa là "nhiều năm").
    `wn._morphy()` trả về toàn bộ ứng viên để ta tự chọn.
    """
    candidates: set[str] = set()
    for pos in ("n", "v", "a", "r"):
        try:
            candidates.update(wn._morphy(word, pos))
        except AttributeError:  # phòng khi NLTK đổi API nội bộ
            single = wn.morphy(word, pos)
            if single:
                candidates.add(single)
    return candidates


def lemmatize(word: str, zipf: Callable[[str], float]) -> str:
    """Quy dạng biến thể về dạng gốc: years→year, took→take, best→good.

    App học từ vựng không nên coi "year" và "years" là hai mục riêng, và
    vi.wiktionary cũng chỉ có mục cho dạng gốc.
    """
    alternatives = [c for c in _morphy_candidates(word) if c != word]
    if not alternatives:
        return word

    best = max(alternatives, key=lambda c: (zipf(c), -len(c)))
    return best if zipf(best) >= zipf(word) - LEMMA_ZIPF_MARGIN else word


def lookup(headword: str, *, max_senses: int = 3) -> list[WordNetSense]:
    """Trả về tối đa `max_senses` nghĩa, mỗi loại từ một nghĩa, đã xếp hạng.

    ⚠️ KHÔNG dùng thứ tự mặc định của `wn.synsets()`. Thứ tự đó đưa danh từ lên
    trước bất kể thực tế, khiến "get" bị định nghĩa thành thuật ngữ quần vợt và
    "see" thành toà giám mục. Thay vào đó xếp hạng theo số lần xuất hiện thật
    trong corpus SemCor (`lemma.count()`) — đây chính là lỗi phân loại mà nhiều
    app đối thủ đang mắc phải.
    """
    lowered = headword.lower()
    scored: list[tuple[int, int, WordNetSense]] = []

    for order, synset in enumerate(wn.synsets(headword)):
        pos = POS_LABEL.get(synset.pos())
        if pos is None:
            continue

        # Bỏ synset là thực thể có tên riêng (Texas, Russia, Christmas…).
        # WordNet đánh dấu chúng bằng instance_hypernyms thay vì hypernyms.
        if synset.instance_hypernyms():
            continue

        frequency = sum(
            lemma.count()
            for lemma in synset.lemmas()
            if lemma.name().lower() == lowered
        )
        synonyms = [
            lemma.name().replace("_", " ")
            for lemma in synset.lemmas()
            if lemma.name().lower() != lowered
        ]
        examples = synset.examples()

        scored.append((
            frequency,
            -order,  # cùng tần suất thì giữ thứ tự gốc của WordNet
            WordNetSense(
                pos=pos,
                definition_en=synset.definition(),
                example_en=examples[0] if examples else None,
                synonyms=synonyms[:5],
                frequency=frequency,
            ),
        ))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

    # Mỗi loại từ chỉ giữ nghĩa mạnh nhất, tránh 3 nghĩa động từ na ná nhau.
    senses: list[WordNetSense] = []
    seen_pos: set[str] = set()
    for _, _, sense in scored:
        if sense.pos in seen_pos:
            continue
        seen_pos.add(sense.pos)
        senses.append(sense)
        if len(senses) >= max_senses:
            break

    return senses


def pick_sense(senses: list[WordNetSense], preferred_pos: str | None) -> WordNetSense:
    """Chọn nghĩa chính, ưu tiên loại từ khớp với nghĩa tiếng Việt tìm được.

    Khớp loại từ giữa hai ngôn ngữ giúp nghĩa Anh và nghĩa Việt nói về CÙNG một
    nghĩa, thay vì nghĩa Anh là danh từ còn nghĩa Việt là động từ.
    """
    if preferred_pos:
        for sense in senses:
            if sense.pos == preferred_pos:
                return sense
    return senses[0]
