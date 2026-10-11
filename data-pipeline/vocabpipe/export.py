"""Xuất dataset ra SQLite (đóng gói vào app) + JSON (để xem/kiểm tra bằng mắt)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .decks import Deck
from .models import Word

SCHEMA = """
PRAGMA journal_mode = DELETE;

DROP TABLE IF EXISTS deck_words;
DROP TABLE IF EXISTS decks;
DROP TABLE IF EXISTS words;
DROP TABLE IF EXISTS meta;

CREATE TABLE words (
    id                INTEGER PRIMARY KEY,
    headword          TEXT    NOT NULL UNIQUE,
    rank              INTEGER NOT NULL,
    zipf              REAL    NOT NULL,
    cefr              TEXT    NOT NULL,
    pos               TEXT,
    pos_vi            TEXT,
    ipa_us            TEXT,
    ipa_uk            TEXT,
    definition_en     TEXT,
    definition_vi     TEXT,
    definition_vi_alt TEXT,
    vi_source         TEXT,
    example_en        TEXT,
    synonyms          TEXT
);

CREATE INDEX idx_words_rank ON words(rank);
CREATE INDEX idx_words_cefr ON words(cefr);

CREATE TABLE decks (
    id              INTEGER PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    name_vi         TEXT NOT NULL,
    description_vi  TEXT,
    cefr            TEXT,
    word_count      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE deck_words (
    deck_id  INTEGER NOT NULL REFERENCES decks(id),
    word_id  INTEGER NOT NULL REFERENCES words(id),
    position INTEGER NOT NULL,
    PRIMARY KEY (deck_id, word_id)
);

CREATE INDEX idx_deck_words_deck ON deck_words(deck_id, position);

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

ATTRIBUTIONS = """# Nguồn dữ liệu & giấy phép

Tệp này được pipeline sinh tự động. **Bắt buộc hiển thị nội dung tương đương
trong app** (ví dụ ở màn hình Cài đặt > Giới thiệu > Nguồn dữ liệu).

## WordNet (Princeton University)

Định nghĩa tiếng Anh, loại từ, câu ví dụ và từ đồng nghĩa lấy từ WordNet.

> WordNet 3.0 Copyright 2006 by Princeton University. All rights reserved.

Giấy phép WordNet cho phép dùng thương mại, miễn phí bản quyền, với điều kiện
giữ nguyên thông báo bản quyền ở trên.
Chi tiết: https://wordnet.princeton.edu/license-and-commercial-use

## Wiktionary (Wikimedia Foundation)

Nghĩa tiếng Việt lấy từ **vi.wiktionary.org**; phiên âm IPA lấy từ
**en.wiktionary.org**.

Nội dung Wiktionary phát hành theo **CC BY-SA 4.0**:
https://creativecommons.org/licenses/by-sa/4.0/

Nghĩa vụ kèm theo:
- Ghi nguồn Wiktionary (đã làm trong tệp này + trong app).
- **Share-alike**: nếu bạn phân phối lại phần DỮ LIỆU đã chỉnh sửa, phần dữ
  liệu đó phải tiếp tục dùng CC BY-SA. Điều này **không** ràng buộc mã nguồn
  app của bạn — chỉ ràng buộc phần dữ liệu từ điển.

## wordfreq

Dữ liệu tần suất từ dùng để xếp hạng và ước lượng cấp độ CEFR.
https://github.com/rspeer/wordfreq — giấy phép MIT.

## Lưu ý về nguồn KHÔNG được dùng

- **Oxford 3000/5000**: Oxford University Press không công bố giấy phép cho
  phép tải về hoặc dùng thương mại. Pipeline này **không** dùng.
- **COCA bản đầy đủ**: cần mua giấy phép thương mại. Pipeline này **không** dùng.
- **Merriam-Webster API**: gói miễn phí chỉ dành cho mục đích phi thương mại.
- **Danh sách TOEIC/IELTS trôi nổi trên mạng**: thường là bản biên soạn có bản
  quyền. Các deck TOEIC/IELTS trong `curated/` phải do bạn tự biên soạn hoặc
  lấy từ nguồn có giấy phép rõ ràng.
"""


def write_sqlite(path: Path, words: list[Word], decks: list[Deck], meta: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)

        word_ids: dict[str, int] = {}
        for index, word in enumerate(words, start=1):
            conn.execute(
                """
                INSERT INTO words (
                    id, headword, rank, zipf, cefr, pos, pos_vi, ipa_us, ipa_uk,
                    definition_en, definition_vi, definition_vi_alt, vi_source,
                    example_en, synonyms
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    index, word.headword, word.rank, word.zipf, word.cefr,
                    word.pos, word.pos_vi, word.ipa_us, word.ipa_uk,
                    word.definition_en, word.definition_vi,
                    json.dumps(word.definition_vi_alt, ensure_ascii=False),
                    word.vi_source, word.example_en,
                    json.dumps(word.synonyms, ensure_ascii=False),
                ),
            )
            word_ids[word.headword] = index

        for deck_index, deck in enumerate(decks, start=1):
            members = [hw for hw in deck.headwords if hw in word_ids]
            conn.execute(
                "INSERT INTO decks (id, slug, name_vi, description_vi, cefr, word_count) "
                "VALUES (?,?,?,?,?,?)",
                (deck_index, deck.slug, deck.name_vi, deck.description_vi,
                 deck.cefr, len(members)),
            )
            conn.executemany(
                "INSERT INTO deck_words (deck_id, word_id, position) VALUES (?,?,?)",
                [(deck_index, word_ids[hw], pos) for pos, hw in enumerate(members)],
            )

        conn.executemany(
            "INSERT INTO meta (key, value) VALUES (?,?)",
            list(meta.items()),
        )
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()


def write_json(path: Path, words: list[Word], decks: list[Deck], meta: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta,
        "decks": [
            {
                "slug": deck.slug,
                "name_vi": deck.name_vi,
                "description_vi": deck.description_vi,
                "cefr": deck.cefr,
                "word_count": len(deck.headwords),
                "headwords": deck.headwords,
            }
            for deck in decks
        ],
        "words": [word.to_dict() for word in words],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_attributions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ATTRIBUTIONS, encoding="utf-8")
