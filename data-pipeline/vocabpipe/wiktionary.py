"""Lấy phiên âm IPA (en.wiktionary) và nghĩa tiếng Việt (vi.wiktionary).

Vì sao dùng vi.wiktionary thay vì bảng Translations của en.wiktionary:
vi.wiktionary có hẳn mục từ tiếng Anh kèm ĐỊNH NGHĨA tiếng Việt (không chỉ là
từ tương đương), chất lượng cao hơn nhiều cho mục đích học từ vựng.

Giấy phép: toàn bộ nội dung Wiktionary là CC BY-SA 4.0 — BẮT BUỘC ghi nguồn
trong app (xem out/ATTRIBUTIONS.md do pipeline tự sinh).

Lịch sự với máy chủ Wikimedia:
- Gộp tối đa 50 trang mỗi request (API cho phép).
- Có cache SQLite nên mỗi trang chỉ tải đúng 1 lần.
- User-Agent mô tả rõ + email liên hệ (theo yêu cầu của Wikimedia).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import requests

from .cache import HttpCache

# ⚠️ ĐỔI email này thành của bạn. Wikimedia yêu cầu User-Agent có liên hệ thật.
USER_AGENT = "VocabWidgetPipeline/0.1 (https://example.com; you@example.com)"

BATCH_SIZE = 50
SLEEP_BETWEEN_BATCHES = 1.0
MAX_ATTEMPTS = 5
INITIAL_BACKOFF = 2.0

# --- Mẫu regex -------------------------------------------------------------

IPA_TEMPLATE = re.compile(r"\{\{IPA\|en\|([^}]+)\}\}")
IPA_VALUE = re.compile(r"/[^/|]+/|\[[^\]|]+\]")
ACCENT_TEMPLATE = re.compile(r"\{\{a\|([^}]+)\}\}")
VI_TRANSLATION = re.compile(r"\{\{t[+\-]?\|vi\|([^}|]+)")

US_MARKERS = {"us", "ga", "genam", "gena", "america", "american"}
UK_MARKERS = {"uk", "rp", "received pronunciation", "britain", "british"}

# vi.wiktionary dùng template kiểu {{-eng-}} cho ngôn ngữ, {{-noun-}} cho loại từ.
VI_LANG_SECTION = re.compile(r"\{\{-(eng|en)-\}\}")
VI_SECTION = re.compile(r"\{\{-([a-z0-9-]+)-\}\}")
VI_HEADING_ENG = re.compile(r"==\s*Tiếng Anh\s*==")
VI_HEADING_ANY = re.compile(r"^==\s*[^=].*?\s*==\s*$", re.MULTILINE)

# Template loại từ. Lưu ý vi.wiktionary tách động từ thành nội động từ
# ({{-intr-verb-}}) và ngoại động từ ({{-trans-verb-}}) — bỏ sót hai cái này
# khiến hầu hết động từ bị gán nhầm thành danh từ.
VI_POS_MAP = {
    "noun": "noun",
    "proper-noun": "noun",
    "verb": "verb",
    "intr-verb": "verb",
    "trans-verb": "verb",
    "intrans-verb": "verb",
    "adj": "adj",
    "adv": "adv",
    "prep": "prep",
    "conj": "conj",
    "intj": "intj",
    "num": "num",
    "abbr": "abbr",
    "phrase": "phrase",
    "pronoun": "pronoun",
    "det": "det",
}

# Template KHÔNG phải mã ngôn ngữ. Mọi template {{-xxx-}} khác có 2–3 ký tự đều
# được coi là mốc bắt đầu một ngôn ngữ khác => kết thúc phần tiếng Anh.
# ⚠️ {{-pron-}} trong vi.wiktionary là PHÁT ÂM, không phải đại từ.
VI_NON_LANGUAGE_SECTIONS = {
    "pron", "ref", "syn", "ant", "drv", "rel", "hyp", "hom", "alt", "see",
    "abr", "ybe", "der", "exp", "par", "paro", "usa", "etym", "etymology",
    "expr", "forms", "related", "usage", "anagrams", "decl", "inf", "part",
    "mut", "trans", "wikipedia", "wikisource", "quote", "note",
    *VI_POS_MAP.keys(),
}

# Dọn wiki markup
RE_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
RE_REF = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.DOTALL)
RE_HTML = re.compile(r"<[^>]+>")
RE_PIPED_LINK = re.compile(r"\[\[[^\]|]*\|([^\]]+)\]\]")
RE_LINK = re.compile(r"\[\[([^\]|]+)\]\]")
RE_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
RE_BOLD_ITALIC = re.compile(r"'{2,5}")
RE_SPACES = re.compile(r"\s+")


def clean_wikitext(text: str) -> str:
    """Biến wikitext thành chuỗi hiển thị được cho người dùng cuối."""
    text = RE_COMMENT.sub("", text)
    text = RE_REF.sub("", text)
    text = RE_PIPED_LINK.sub(r"\1", text)
    text = RE_LINK.sub(r"\1", text)

    # Template có thể lồng nhau; lặp vài vòng cho hết.
    for _ in range(4):
        new = RE_TEMPLATE.sub("", text)
        if new == text:
            break
        text = new

    text = RE_HTML.sub("", text)
    text = RE_BOLD_ITALIC.sub("", text)
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&amp;", "&")
    text = RE_SPACES.sub(" ", text)
    return text.strip(" ;:,.-")


# --- Tải wikitext theo lô --------------------------------------------------


class WiktionaryClient:
    def __init__(self, cache: HttpCache, *, user_agent: str = USER_AGENT):
        self._cache = cache
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent

    def _cache_key(self, wiki: str, title: str) -> str:
        return f"{wiki}:{title}"

    def _request_batch(self, url: str, chunk: list[str], progress=None) -> list[dict] | None:
        """Gọi API với retry + backoff luỹ thừa.

        Wikimedia trả 429 khi gọi quá nhanh. Nếu không retry, những từ trong lô
        bị 429 sẽ vĩnh viễn thiếu IPA/nghĩa mà pipeline vẫn báo thành công.
        """
        backoff = INITIAL_BACKOFF

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._session.get(
                    url,
                    params={
                        "action": "query",
                        "prop": "revisions",
                        "rvprop": "content",
                        "rvslots": "main",
                        "format": "json",
                        "formatversion": "2",
                        "titles": "|".join(chunk),
                    },
                    timeout=60,
                )

                if response.status_code == 429 or response.status_code >= 500:
                    wait = backoff
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                    if progress:
                        progress(f"  . bị giới hạn tốc độ ({response.status_code}), "
                                 f"chờ {wait:.0f}s rồi thử lại ({attempt}/{MAX_ATTEMPTS})")
                    time.sleep(wait)
                    backoff *= 2
                    continue

                response.raise_for_status()
                return response.json().get("query", {}).get("pages", [])

            except (requests.RequestException, ValueError) as error:
                if attempt == MAX_ATTEMPTS:
                    if progress:
                        progress(f"  ! bỏ qua lô sau {MAX_ATTEMPTS} lần thử: {error}")
                    return None
                time.sleep(backoff)
                backoff *= 2

        if progress:
            progress(f"  ! bỏ qua lô sau {MAX_ATTEMPTS} lần thử (vẫn bị giới hạn tốc độ)")
        return None

    def fetch_many(self, wiki: str, titles: list[str], *, progress=None) -> None:
        """Tải và cache wikitext của nhiều trang. `wiki` là 'en' hoặc 'vi'."""
        pending = [t for t in titles if not self._cache.has(self._cache_key(wiki, t))]
        if not pending:
            return

        url = f"https://{wiki}.wiktionary.org/w/api.php"

        for start in range(0, len(pending), BATCH_SIZE):
            chunk = pending[start:start + BATCH_SIZE]
            pages = self._request_batch(url, chunk, progress)

            # Lô thất bại: KHÔNG ghi cache, để lần chạy sau thử lại.
            if pages is None:
                continue

            returned: set[str] = set()
            for page in pages:
                title = page.get("title", "")
                returned.add(title)
                if page.get("missing"):
                    self._cache.put(self._cache_key(wiki, title), None)
                    continue
                try:
                    content = page["revisions"][0]["slots"]["main"]["content"]
                except (KeyError, IndexError):
                    content = None
                self._cache.put(self._cache_key(wiki, title), content)

            # Trang được chuẩn hoá tên (ví dụ viết hoa) sẽ không khớp title gốc.
            for title in chunk:
                if title not in returned and not self._cache.has(self._cache_key(wiki, title)):
                    self._cache.put(self._cache_key(wiki, title), None)

            if progress:
                progress(f"  {wiki}.wiktionary: {min(start + BATCH_SIZE, len(pending))}/{len(pending)}")
            time.sleep(SLEEP_BETWEEN_BATCHES)

    def wikitext(self, wiki: str, title: str) -> str | None:
        return self._cache.get(self._cache_key(wiki, title))


# --- Bóc tách --------------------------------------------------------------


@dataclass
class Pronunciation:
    ipa_us: str | None = None
    ipa_uk: str | None = None

    @property
    def primary(self) -> str | None:
        return self.ipa_us or self.ipa_uk


def parse_pronunciation(wikitext_en: str | None) -> Pronunciation:
    result = Pronunciation()
    if not wikitext_en:
        return result

    generic: str | None = None

    for line in wikitext_en.splitlines():
        match = IPA_TEMPLATE.search(line)
        if not match:
            continue

        values = IPA_VALUE.findall(match.group(1))
        if not values:
            continue
        value = values[0]

        accents = {
            part.strip().lower()
            for accent in ACCENT_TEMPLATE.findall(line)
            for part in accent.split("|")
        }

        if accents & US_MARKERS and not result.ipa_us:
            result.ipa_us = value
        elif accents & UK_MARKERS and not result.ipa_uk:
            result.ipa_uk = value
        elif generic is None:
            generic = value

    if not result.ipa_us and not result.ipa_uk:
        result.ipa_us = generic

    return result


@dataclass
class VietnameseEntry:
    definitions: list[str] = field(default_factory=list)
    by_pos: dict[str, list[str]] = field(default_factory=dict)
    source: str = ""

    @property
    def primary(self) -> str | None:
        return self.definitions[0] if self.definitions else None


def _is_language_marker(name: str) -> bool:
    return len(name) in (2, 3) and name not in VI_NON_LANGUAGE_SECTIONS


def _english_section(wikitext_vi: str) -> str | None:
    """Cắt lấy phần mục từ tiếng Anh trong trang vi.wiktionary."""
    match = VI_LANG_SECTION.search(wikitext_vi)
    if match:
        rest = wikitext_vi[match.end():]
        for section in VI_SECTION.finditer(rest):
            if _is_language_marker(section.group(1)):
                return rest[:section.start()]
        return rest

    match = VI_HEADING_ENG.search(wikitext_vi)
    if match:
        rest = wikitext_vi[match.end():]
        next_heading = VI_HEADING_ANY.search(rest)
        return rest[:next_heading.start()] if next_heading else rest

    return None


def _definition_lines(section: str) -> list[tuple[str, str]]:
    """Trả về danh sách (loại từ, định nghĩa) theo đúng thứ tự xuất hiện."""
    results: list[tuple[str, str]] = []
    current_pos: str | None = None

    for raw_line in section.splitlines():
        line = raw_line.strip()

        marker = VI_SECTION.search(line)
        if marker:
            # Vào mục không phải loại từ (phát âm, từ đồng nghĩa, thành ngữ…)
            # thì ngừng thu thập, tránh nhặt nhầm thành ngữ thành định nghĩa.
            current_pos = VI_POS_MAP.get(marker.group(1))
            continue

        # '#' là dòng định nghĩa; '#:' là ví dụ, '#*' là trích dẫn — bỏ qua.
        if not line.startswith("#") or line.startswith(("#:", "#*", "##")):
            continue
        if current_pos is None:
            continue

        text = clean_wikitext(line.lstrip("#").strip())
        if len(text) >= 2:
            results.append((current_pos, text))

    return results


def parse_vietnamese(wikitext_vi: str | None, *, max_per_pos: int = 2) -> VietnameseEntry:
    entry = VietnameseEntry()
    if not wikitext_vi:
        return entry

    section = _english_section(wikitext_vi)
    if section is None:
        return entry

    for pos, text in _definition_lines(section):
        bucket = entry.by_pos.setdefault(pos, [])
        if len(bucket) < max_per_pos:
            bucket.append(text)
        if text not in entry.definitions:
            entry.definitions.append(text)

    if entry.definitions:
        entry.source = "vi.wiktionary"
    return entry


def parse_vietnamese_fallback(wikitext_en: str | None) -> VietnameseEntry:
    """Phương án dự phòng: lấy từ tương đương trong bảng Translations của en.wiktionary."""
    entry = VietnameseEntry()
    if not wikitext_en:
        return entry

    seen: set[str] = set()
    for raw in VI_TRANSLATION.findall(wikitext_en):
        text = clean_wikitext(raw)
        if text and text.lower() not in seen:
            seen.add(text.lower())
            entry.definitions.append(text)

    if entry.definitions:
        entry.by_pos["unknown"] = entry.definitions[:3]
        entry.source = "en.wiktionary/translations"
    return entry


def needs_translation_subpage(wikitext_en: str | None) -> bool:
    """en.wiktionary tách bảng dịch quá lớn sang trang con `<từ>/translations`."""
    if not wikitext_en:
        return False
    return "translation subpage" in wikitext_en or "{{trans-see" in wikitext_en
