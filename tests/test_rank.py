"""Tests for core.rank — index-free two-stage retrieval over Zotero's full-text index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from zotero_cli_cc.core.rank import (
    extract_passages,
    make_snippet,
    rank,
    reciprocal_rank_fusion,
    resolve_collection_key,
    tokenize,
)
from zotero_cli_cc.core.reader import ZoteroReader

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def reader():
    r = ZoteroReader(FIXTURES_DIR / "zotero.sqlite")
    yield r
    r.close()


class TestTokenize:
    def test_strips_punctuation_and_lowercases(self):
        assert tokenize("Hello, world! (Attention)") == ["hello", "world", "attention"]


class TestExtractPassages:
    def test_carves_window_around_hit(self):
        text = "alpha " * 100 + "transformer" + " omega " * 100
        passages = extract_passages(text, ["transformer"], max_passages=1, window=50)
        assert len(passages) == 1
        assert "transformer" in passages[0]
        assert len(passages[0]) <= 110

    def test_no_hit_returns_empty(self):
        assert extract_passages("nothing here", ["quantum"]) == []

    def test_respects_max_passages(self):
        passages = extract_passages("hit " * 50, ["hit"], max_passages=2, window=20)
        assert 1 <= len(passages) <= 2


class TestReciprocalRankFusion:
    def test_fuses_rankings(self):
        fused = reciprocal_rank_fusion([("a", 10.0), ("b", 5.0)], [("b", 1.0), ("c", 0.5)])
        keys = [k for k, _ in fused]
        assert keys[0] == "b"  # 2nd in one ranking + 1st in the other beats a single 1st
        assert set(keys) == {"a", "b", "c"}

    def test_empty(self):
        assert reciprocal_rank_fusion([], []) == []


class TestRank:
    def test_fulltext_and_metadata_fused(self, reader):
        results = rank(reader, "transformer attention", top_k=5)
        assert results[0]["item"].key == "ATTN001"
        assert results[0]["scores"]["fulltext"] is not None
        assert results[0]["scores"]["metadata"] is not None

    def test_collection_scope_by_name(self, reader):
        col_key = resolve_collection_key(reader, "Transformers")
        assert col_key == "COLTR02"
        results = rank(reader, "transformer attention", collection_key=col_key, top_k=5)
        assert [r["item"].key for r in results] == ["ATTN001"]

    def test_collection_scope_by_key(self, reader):
        results = rank(reader, "transformer attention", collection_key="COLTR02", top_k=5)
        assert [r["item"].key for r in results] == ["ATTN001"]

    def test_unknown_collection_returns_empty(self, reader):
        assert rank(reader, "transformer", collection_key="NOPE9999", top_k=5) == []

    def test_no_match_returns_empty(self, reader):
        assert rank(reader, "zzzznotfound", top_k=5) == []

    def test_library_isolation(self, reader):
        # 'protein' only exists in the group library (libraryID 2); the default
        # user-library reader must not see it, in either fulltext or metadata.
        assert rank(reader, "protein", top_k=5) == []

    def test_snippet_from_abstract(self, reader):
        results = rank(reader, "transformer attention", top_k=1)
        assert make_snippet(results[0]["item"], results[0]["terms"])


class TestRankWithSecondIndexedAttachment:
    """Term coverage differentiates items once a second PDF is indexed."""

    @pytest.fixture
    def reader_two_pdfs(self, tmp_path):
        dst = tmp_path / "zotero.sqlite"
        dst.write_bytes((FIXTURES_DIR / "zotero.sqlite").read_bytes())
        conn = sqlite3.connect(dst)
        conn.execute("INSERT INTO items VALUES (20, 14, '2024-02-03', '2024-02-03', '2024-02-03', 1, 'ATCH020')")
        conn.execute("INSERT INTO itemAttachments VALUES (20, 2, 0, 'application/pdf', NULL, 'storage:bert.pdf')")
        conn.execute("INSERT INTO fulltextItemWords VALUES (1, 20)")  # only 'transformer'
        conn.execute("INSERT INTO fulltextItems VALUES (20, 20, 20, 8000, 8000, 1, 0)")
        conn.commit()
        conn.close()
        r = ZoteroReader(dst)
        yield r
        r.close()

    def test_more_fulltext_terms_ranks_higher(self, reader_two_pdfs):
        results = rank(reader_two_pdfs, "transformer attention mechanism", top_k=5)
        keys = [r["item"].key for r in results]
        assert keys[0] == "ATTN001"  # 3 fulltext terms vs 1 for BERT002
        assert "BERT002" in keys
