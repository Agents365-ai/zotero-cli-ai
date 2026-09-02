import os
import sqlite3
from pathlib import Path

import pytest

from zotero_cli_cc.core.pdf_cache import PdfCache


@pytest.fixture
def cache(tmp_path: Path) -> PdfCache:
    return PdfCache(tmp_path / "pdf_cache.sqlite")


def test_cache_miss(cache: PdfCache, tmp_path: Path) -> None:
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"fake pdf")
    assert cache.get(pdf) is None


def test_cache_put_and_get(cache: PdfCache, tmp_path: Path) -> None:
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"fake pdf")
    cache.put(pdf, "extracted text content")
    assert cache.get(pdf) == "extracted text content"


def test_cache_invalidation_on_mtime_change(cache: PdfCache, tmp_path: Path) -> None:
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"fake pdf v1")
    cache.put(pdf, "v1 text")
    pdf.write_bytes(b"fake pdf v2")
    # Bump mtime deterministically instead of sleeping for the fs timestamp to tick
    st = pdf.stat()
    os.utime(pdf, (st.st_atime, st.st_mtime + 10))
    assert cache.get(pdf) is None


def test_cache_clear(cache: PdfCache, tmp_path: Path) -> None:
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"fake pdf")
    cache.put(pdf, "text")
    cache.clear()
    assert cache.get(pdf) is None


def test_cache_stats(cache: PdfCache, tmp_path: Path) -> None:
    pdf1 = tmp_path / "a.pdf"
    pdf1.write_bytes(b"a")
    pdf2 = tmp_path / "b.pdf"
    pdf2.write_bytes(b"b")
    cache.put(pdf1, "text a")
    cache.put(pdf2, "text b")
    stats = cache.stats()
    assert stats["entries"] == 2
    assert stats["total_chars"] > 0


def test_migrates_legacy_schema_without_extractor_column(tmp_path: Path) -> None:
    """Cache DBs created before the extractor column must be upgraded in place."""
    legacy = tmp_path / "pdf_cache.sqlite"
    conn = sqlite3.connect(str(legacy))
    conn.execute(
        "CREATE TABLE pdf_cache ("
        "  pdf_path TEXT PRIMARY KEY, mtime REAL NOT NULL,"
        "  content TEXT NOT NULL, extracted_at TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"fake pdf")
    cache = PdfCache(legacy)
    cache.put(pdf, "pdfium", "text")
    assert cache.get(pdf, "pdfium") == "text"
    cache.close()
