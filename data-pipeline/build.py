#!/usr/bin/env python3
"""Dựng dataset từ vựng Anh–Việt cho app widget học từ vựng.

Luồng chạy:
    tần suất (wordfreq)  ->  nghĩa tiếng Anh (WordNet)
                         ->  IPA (en.wiktionary) + nghĩa tiếng Việt (vi.wiktionary)
                         ->  gom thành deck
                         ->  xuất SQLite + JSON + ATTRIBUTIONS.md

Ví dụ:
    python build.py --limit 200              # chạy thử nhanh
    python build.py --limit 3000             # dựng bộ thật
    python build.py --limit 3000 --offline   # chỉ dùng cache, không gọi mạng
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

from vocabpipe import decks as decks_mod
from vocabpipe import export, frequency, wiktionary, wordnet_source
from vocabpipe.cache import HttpCache
from vocabpipe.models import Word

ROOT = Path(__file__).resolve().parent


def log(message: str = "") -> None:
    print(message, flush=True)


def build(args: argparse.Namespace) -> int:
    started = time.time()

    out_dir = Path(args.out)
    curated_dir = Path(args.curated)
    cache_path = Path(args.cache)

    # --- 1. Chọn từ ứng viên theo tần suất -------------------------------
    log(f"[1/5] Chọn {args.limit} từ phổ biến nhất…")
    wordnet_source.ensure_corpus()

    from functools import lru_cache

    from wordfreq import zipf_frequency

    @lru_cache(maxsize=None)
    def zipf(word: str) -> float:
        return zipf_frequency(word, "en")

    def lemmatizer(word: str) -> str:
        return wordnet_source.lemmatize(word, zipf)

    candidates = frequency.candidates(
        args.limit,
        lemmatizer=None if args.no_lemmatize else lemmatizer,
    )
    log(f"      {len(candidates)} ứng viên (rank 1–{candidates[-1].rank if candidates else 0})")

    # --- 2. Nghĩa tiếng Anh từ WordNet -----------------------------------
    log("[2/5] Tra WordNet…")

    words: list[Word] = []
    senses_by_word: dict[str, list[wordnet_source.WordNetSense]] = {}
    skipped_no_wordnet = 0

    for candidate in candidates:
        senses = wordnet_source.lookup(candidate.headword, max_senses=args.max_senses)
        if not senses:
            skipped_no_wordnet += 1
            continue

        senses_by_word[candidate.headword] = senses
        words.append(
            Word(
                headword=candidate.headword,
                rank=candidate.rank,
                zipf=candidate.zipf,
                cefr=candidate.cefr,
            )
        )

    log(f"      {len(words)} từ có định nghĩa WordNet "
        f"({skipped_no_wordnet} từ bị loại vì không có)")

    if not words:
        log("Không có từ nào — dừng.")
        return 1

    # --- 3. Wiktionary: IPA + nghĩa tiếng Việt ---------------------------
    log("[3/5] Tra Wiktionary (IPA + nghĩa tiếng Việt)…")
    cache = HttpCache(cache_path)
    client = wiktionary.WiktionaryClient(cache, user_agent=args.user_agent)
    titles = [word.headword for word in words]

    if args.offline:
        log("      chế độ offline — chỉ dùng cache")
    else:
        client.fetch_many("en", titles, progress=log)
        client.fetch_many("vi", titles, progress=log)

    # Trang có bảng dịch quá lớn bị tách sang trang con `<từ>/translations`.
    subpages = [
        f"{word.headword}/translations"
        for word in words
        if wiktionary.needs_translation_subpage(client.wikitext("en", word.headword))
    ]
    if subpages and not args.offline:
        log(f"      {len(subpages)} từ có trang con /translations…")
        client.fetch_many("en", subpages, progress=log)

    vi_sources: Counter[str] = Counter()
    pos_aligned = 0
    needs_review: list[tuple[str, str, str, str]] = []

    for word in words:
        en_text = client.wikitext("en", word.headword)
        vi_text = client.wikitext("vi", word.headword)

        pronunciation = wiktionary.parse_pronunciation(en_text)
        word.ipa_us = pronunciation.ipa_us
        word.ipa_uk = pronunciation.ipa_uk

        entry = wiktionary.parse_vietnamese(vi_text)
        if not entry.definitions:
            entry = wiktionary.parse_vietnamese_fallback(en_text)
        if not entry.definitions:
            sub_text = client.wikitext("en", f"{word.headword}/translations")
            entry = wiktionary.parse_vietnamese_fallback(sub_text)

        senses = senses_by_word[word.headword]
        sense_by_pos = {sense.pos: sense for sense in senses}

        # Khớp loại từ giữa hai ngôn ngữ: chỉ xét những loại từ mà CẢ WordNet và
        # vi.wiktionary đều có, rồi trong số đó chọn loại từ dùng nhiều nhất theo
        # corpus SemCor. Nhờ vậy "get" ra động từ chứ không phải thuật ngữ quần vợt,
        # và "make" ra động từ chứ không phải danh từ "kiểu dáng".
        shared_pos = [pos for pos in entry.by_pos if pos in sense_by_pos]
        preferred_pos = max(
            shared_pos,
            key=lambda pos: sense_by_pos[pos].frequency,
            default=None,
        )
        if preferred_pos and preferred_pos != senses[0].pos:
            pos_aligned += 1

        sense = wordnet_source.pick_sense(senses, preferred_pos)

        # Nếu loại từ được chọn yếu hơn hẳn loại từ phổ biến nhất của WordNet,
        # nghĩa là vi.wiktionary thiếu mục đó (ví dụ "make" chỉ có mục danh từ).
        # Nghĩa xuất ra vẫn nhất quán Anh–Việt, nhưng KHÔNG phải nghĩa chính —
        # đánh dấu để người biên tập soát lại thay vì âm thầm cho qua.
        dominant = senses[0]
        if sense.pos != dominant.pos and sense.frequency * 3 < dominant.frequency:
            needs_review.append((
                word.headword,
                f"{sense.pos} (chọn, freq={sense.frequency})",
                f"{dominant.pos} (phổ biến hơn, freq={dominant.frequency})",
                dominant.definition_en,
            ))

        word.pos = sense.pos
        word.pos_vi = wordnet_source.POS_LABEL_VI.get(sense.pos)
        word.definition_en = sense.definition_en
        word.example_en = sense.example_en
        word.synonyms = sense.synonyms

        if entry.definitions:
            # Ưu tiên nghĩa tiếng Việt thuộc đúng loại từ đã chọn.
            bucket = entry.by_pos.get(sense.pos) or entry.definitions
            word.definition_vi = bucket[0]
            word.definition_vi_alt = [d for d in entry.definitions if d != bucket[0]][:3]
            word.vi_source = entry.source
            vi_sources[entry.source] += 1
        else:
            vi_sources["(không có)"] += 1

    cache_stats = cache.stats()
    cache.close()

    log(f"      cache: {cache_stats['hits']} trang có nội dung / "
        f"{cache_stats['misses']} trang không tồn tại")
    log(f"      {pos_aligned} từ được sửa loại từ nhờ khớp với vi.wiktionary")
    log(f"      {len(needs_review)} từ cần soát loại từ thủ công")
    for source, count in vi_sources.most_common():
        log(f"      nghĩa tiếng Việt từ {source}: {count}")

    # --- 4. Lọc & gom deck ----------------------------------------------
    log("[4/5] Lọc và gom deck…")

    complete = [word for word in words if word.is_complete]
    incomplete = [word for word in words if not word.is_complete]

    log(f"      {len(complete)} từ ĐẦY ĐỦ (có cả nghĩa Anh và Việt)")
    log(f"      {len(incomplete)} từ thiếu nghĩa tiếng Việt → cần bổ sung thủ công")

    selected = complete if not args.include_incomplete else words

    # Đánh lại rank liên tục sau khi lọc, để deck theo rank không bị thủng.
    for position, word in enumerate(selected, start=1):
        word.rank = position

    deck_list = decks_mod.build_all(selected, curated_dir)
    for deck in deck_list:
        log(f"      deck {deck.slug:<14} {len(deck.headwords):>5} từ  ({deck.name_vi})")

    # --- 5. Xuất ----------------------------------------------------------
    log("[5/5] Xuất dữ liệu…")

    ipa_count = sum(1 for word in selected if word.ipa_us or word.ipa_uk)
    example_count = sum(1 for word in selected if word.example_en)

    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "word_count": str(len(selected)),
        "deck_count": str(len(deck_list)),
        "sources": "WordNet 3.0 (Princeton); Wiktionary (CC BY-SA 4.0); wordfreq (MIT)",
        "license_note": "Xem ATTRIBUTIONS.md — bắt buộc hiển thị trong app",
    }

    sqlite_path = out_dir / "vocab.sqlite"
    json_path = out_dir / "vocab.json"
    missing_path = out_dir / "missing-vietnamese.txt"
    review_path = out_dir / "needs-review.txt"

    export.write_sqlite(sqlite_path, selected, deck_list, meta)
    export.write_json(json_path, selected, deck_list, meta)
    export.write_attributions(out_dir / "ATTRIBUTIONS.md")

    missing_path.write_text(
        "\n".join(
            f"{word.headword}\t{word.pos}\t{word.definition_en}"
            for word in incomplete
        ),
        encoding="utf-8",
    )

    review_path.write_text(
        "# Từ cần soát loại từ thủ công\n"
        "# vi.wiktionary thiếu mục của loại từ phổ biến nhất, nên nghĩa xuất ra\n"
        "# tuy nhất quán Anh-Việt nhưng không phải nghĩa chính của từ.\n"
        "# Cột: từ | loại từ đã chọn | loại từ phổ biến hơn | nghĩa EN của loại từ đó\n\n"
        + "\n".join("\t".join(row) for row in needs_review),
        encoding="utf-8",
    )

    log()
    log("─" * 60)
    log(f"Tổng số từ xuất ra      : {len(selected)}")
    log(f"Có phiên âm IPA         : {ipa_count} ({ipa_count * 100 // max(len(selected), 1)}%)")
    log(f"Có câu ví dụ tiếng Anh  : {example_count} ({example_count * 100 // max(len(selected), 1)}%)")
    log(f"Số deck                 : {len(deck_list)}")
    log(f"SQLite                  : {sqlite_path}  ({sqlite_path.stat().st_size // 1024} KB)")
    log(f"JSON                    : {json_path}  ({json_path.stat().st_size // 1024} KB)")
    log(f"Từ thiếu nghĩa Việt     : {missing_path}  ({len(incomplete)} từ)")
    log(f"Từ cần soát loại từ     : {review_path}  ({len(needs_review)} từ)")
    log(f"Thời gian               : {time.time() - started:.1f}s")
    log("─" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=500,
                        help="số từ phổ biến nhất cần xử lý (mặc định 500)")
    parser.add_argument("--max-senses", type=int, default=3,
                        help="số nghĩa WordNet lấy tối đa cho mỗi từ")
    parser.add_argument("--out", default=str(ROOT / "out"),
                        help="thư mục xuất kết quả")
    parser.add_argument("--curated", default=str(ROOT / "curated"),
                        help="thư mục chứa deck tự biên soạn")
    parser.add_argument("--cache", default=str(ROOT / "out" / "http-cache.sqlite"),
                        help="file cache HTTP")
    parser.add_argument("--offline", action="store_true",
                        help="không gọi mạng, chỉ dùng cache đã có")
    parser.add_argument("--include-incomplete", action="store_true",
                        help="xuất cả từ chưa có nghĩa tiếng Việt")
    parser.add_argument("--no-lemmatize", action="store_true",
                        help="không quy dạng biến thể về dạng gốc (years -> year)")
    parser.add_argument("--user-agent", default=wiktionary.USER_AGENT,
                        help="User-Agent gửi lên Wikimedia (nên có email liên hệ)")

    return build(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
