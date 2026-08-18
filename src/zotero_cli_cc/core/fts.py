"""Query-side helpers for Zotero 10's FTS5 full-text index (fulltext.sqlite).

Zotero 10 moved the full-text index out of zotero.sqlite into a separate
``fulltext.sqlite`` (contentless FTS5 tables keyed by attachment itemID) and
dropped the legacy ``fulltextWords``/``fulltextItemWords`` tables. This module
ports the query-side semantics of Zotero 10's ``fulltext.js`` so zot builds
MATCH expressions exactly the way the app does:

- terms are normalized like ``normalizeForSearch`` (NFKD, strip combining
  diacritics, lowercase, fold a handful of Latin specials plus typographic
  quotes/dashes to ASCII, recompose NFC) — the indexed text is stored in the
  same normalized form;
- a pure-CJK term is matched against the ascii-tokenized ``fulltextContentCJK``
  table as a quoted phrase of the term's overlapping 2-grams (CJK runs are
  indexed as bigrams, since the word tokenizer treats a CJK run as one token);
- a non-CJK term is matched against the unicode61 ``fulltextContent`` table as
  a quoted token phrase with the final token prefix-matched (``"tokens"*``),
  so "archive" matches "archives";
- mixed-script terms, single CJK characters (no bigram), and terms without
  word characters can't be answered by the index — Zotero falls back to
  scanning cached text files; zot simply skips them.
"""

from __future__ import annotations

import re
import unicodedata

# fulltextIndexState.version marking a fully indexed attachment
# (Zotero 10 fulltext.js: `const _contentIndexVersion = 1`; rows with
# itemID IS NULL or version < 1 are the not-yet-indexed queue).
CONTENT_INDEX_VERSION = 1

# CJK scripts (Han/Hiragana/Katakana/Hangul) — Python's re has no \p{Script=…},
# so the same scripts are spelled out as codepoint ranges.
_CJK_RANGES = (
    "㐀-䶿一-鿿豈-﫿"  # Han (ext A, unified, compat ideographs)
    "\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f"
    "\U0002b820-\U0002ceaf\U0002ceb0-\U0002ebef\U00030000-\U0003134f"
    "\U0002f800-\U0002fa1f"  # Han ext B–H, compat supplement
    "぀-ゟ"  # Hiragana
    "゠-ヿㇰ-ㇿｦ-ﾝ"  # Katakana (+ ext, halfwidth)
    "ᄀ-ᇿ㄰-㆏ꥠ-꥿가-힯ힰ-퟿"  # Hangul (jamo, compat jamo, ext, syllables, ext-B)
)
_CJK_CHAR_RE = re.compile(f"[{_CJK_RANGES}]")
_CJK_RUN_RE = re.compile(f"[{_CJK_RANGES}]+")
# Letters/digits as the unicode61 tokenizer produces them: runs of L*/N*.
_WORD_TOKEN_RE = re.compile(r"[^\W_]+")
_WORD_CHAR_RE = re.compile(r"[^\W_]")

# Zotero's _searchNormalizeMap plus the typographic quote/dash folds (applied
# after lowercasing, so only the lowercase forms appear).
_NORMALIZE_TRANS = str.maketrans(
    {
        "ø": "o",
        "œ": "oe",
        "æ": "ae",
        "ł": "l",
        "đ": "d",
        "ð": "d",
        "þ": "th",
        "ß": "ss",
        "ı": "i",
        "⁄": "/",
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "′": "'",
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "″": '"',
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        "−": "-",
    }
)


def normalize_for_search(text: str) -> str:
    """Port of Zotero's ``normalizeForSearch`` (utilities_internal.js).

    NFKD → strip combining diacritics → lowercase → fold Latin specials and
    typographic quotes/dashes → NFC. Zotero additionally strips a small
    whitelist of rich-text formatting tags; that only matters for item field
    values, not for full-text content or typed query terms, so it is omitted.
    """
    if not text:
        return text
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not (0x0300 <= ord(c) <= 0x036F))
    return unicodedata.normalize("NFC", stripped.lower().translate(_NORMALIZE_TRANS))


def cjk_bigrams(text: str) -> str:
    """Space-separated overlapping 2-grams of the CJK runs in ``text``.

    Port of Zotero's ``getCJKBigrams``: only CJK characters are bigrammed —
    everything else is handled by the word index — so text without CJK runs
    produces an empty string. A single CJK character has no 2-gram.
    """
    bigrams: list[str] = []
    for match in _CJK_RUN_RE.finditer(text):
        run = match.group(0)
        bigrams.extend(run[i : i + 2] for i in range(len(run) - 1))
    return " ".join(bigrams)


def content_match_clause(term: str) -> tuple[str, str] | None:
    """Resolve a search term to (FTS5 table, MATCH expression), Zotero-style.

    Port of Zotero's ``getWordMatchClause`` minus the verification flag: zot
    ranks instead of verifying candidates against cached text. Returns None
    for terms the index can't answer (mixed script, single CJK character, or
    no word characters at all).
    """
    normalized = normalize_for_search(term)
    if not normalized:
        return None
    has_cjk = bool(_CJK_CHAR_RE.search(normalized))
    has_non_cjk = bool(_WORD_CHAR_RE.search(_CJK_RUN_RE.sub("", normalized)))
    # Pure CJK: match the term's 2-grams as a contiguous phrase against the
    # ascii-tokenized CJK index.
    if has_cjk and not has_non_cjk:
        bigrams = cjk_bigrams(normalized)
        if not bigrams:
            return None
        return ("fulltextContentCJK", f'"{bigrams}"')
    if has_cjk:
        # Mixed script: neither index covers the term alone.
        return None
    tokens = _WORD_TOKEN_RE.findall(normalized)
    if not tokens:
        return None
    # Non-CJK: adjacent token phrase against the word index, final token as a
    # prefix. Tokens are letter/digit runs, so no quoting escapes are needed.
    return ("fulltextContent", '"' + " ".join(tokens) + '"*')
