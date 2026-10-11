"""Cache HTTP dạng SQLite.

Mục đích: gọi Wiktionary hàng nghìn lần mà chỉ tải mỗi trang đúng 1 lần.
Chạy lại pipeline lần 2 sẽ gần như tức thì và không làm phiền máy chủ Wikimedia.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path


class HttpCache:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                key        TEXT PRIMARY KEY,
                body       TEXT,
                fetched_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def has(self, key: str) -> bool:
        return self._conn.execute(
            "SELECT 1 FROM pages WHERE key = ?", (key,)
        ).fetchone() is not None

    def get(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT body FROM pages WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def put(self, key: str, body: str | None) -> None:
        # body=None vẫn được lưu: nghĩa là "đã hỏi rồi, trang này không tồn tại".
        self._conn.execute(
            "INSERT OR REPLACE INTO pages (key, body, fetched_at) VALUES (?, ?, ?)",
            (key, body, time.time()),
        )
        self._conn.commit()

    def stats(self) -> dict[str, int]:
        total = self._conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        missing = self._conn.execute(
            "SELECT COUNT(*) FROM pages WHERE body IS NULL"
        ).fetchone()[0]
        return {"total": total, "hits": total - missing, "misses": missing}

    def close(self) -> None:
        self._conn.close()
