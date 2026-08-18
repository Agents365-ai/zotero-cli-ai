"""Tests for core.rank — index-free two-stage retrieval over Zotero's full-text index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from zotero_cli_cc.core.fts import content_match_clause
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


class TestContentMatchClause:
    """MATCH construction ported from Zotero 10's getWordMatchClause."""

    def test_single_token_prefix_matched(self):
        assert content_match_clause("Transformer") == ("fulltextContent", '"transformer"*')

    def test_multi_token_adjacent_phrase(self):
        assert content_match_clause("climate change") == ("fulltextContent", '"climate change"*')

    def test_normalization_folds_diacritics_and_quotes(self):
        assert content_match_clause("Séance’s") == ("fulltextContent", '"seance s"*')

    def test_pure_cjk_routes_to_bigram_table(self):
        assert content_match_clause("自然语言") == ("fulltextContentCJK", '"自然 然语 语言"')

    def test_single_cjk_char_has_no_bigram(self):
        assert content_match_clause("语") is None

    def test_mixed_script_not_indexable(self):
        assert content_match_clause("自然语言processing") is None

    def test_no_word_chars_returns_none(self):
        assert content_match_clause("!!!") is None


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

    def test_stale_index_version_not_counted(self, reader):
        # Attachment 13 has FTS content but fulltextIndexState.version = 0
        # (queued for re-indexing) — it must not count as indexed.
        assert rank(reader, "blockchain", top_k=5) == []

    def test_pure_cjk_term_matches_via_cjk_table(self, reader):
        # 自然语言 only appears in CJKX014's full text (not its metadata), so
        # only the fulltextContentCJK bigram path can find it.
        results = rank(reader, "自然语言", top_k=5)
        assert results[0]["item"].key == "CJKX014"
        assert results[0]["scores"]["fulltext"] is not None
        assert results[0]["scores"]["metadata"] is None

    def test_single_cjk_char_yields_no_fulltext_score(self, reader):
        # A single CJK character has no 2-gram — the index can't answer it.
        results = rank(reader, "语", top_k=5)
        assert all(r["scores"]["fulltext"] is None for r in results)

    def test_snippet_from_abstract(self, reader):
        results = rank(reader, "transformer attention", top_k=1)
        assert make_snippet(results[0]["item"], results[0]["terms"])


class TestRankWithoutFulltextDb:
    """Pre-Zotero 10 data directories (no fulltext.sqlite): metadata-only."""

    @pytest.fixture
    def reader_no_fts(self, tmp_path):
        dst = tmp_path / "zotero.sqlite"
        dst.write_bytes((FIXTURES_DIR / "zotero.sqlite").read_bytes())
        r = ZoteroReader(dst)
        yield r
        r.close()

    def test_warns_and_degrades_to_metadata_only(self, reader_no_fts):
        with pytest.warns(UserWarning, match="fulltext.sqlite"):
            results = rank(reader_no_fts, "transformer attention", top_k=5)
        assert results
        assert results[0]["item"].key == "ATTN001"
        assert all(r["scores"]["fulltext"] is None for r in results)
        assert results[0]["scores"]["metadata"] is not None

    def test_fulltext_candidates_empty(self, reader_no_fts):
        assert reader_no_fts.fulltext_candidates() == []


class TestRankWithSecondIndexedAttachment:
    """bm25 differentiates items once a second PDF is indexed."""

    @pytest.fixture
    def reader_two_pdfs(self, tmp_path):
        dst = tmp_path / "zotero.sqlite"
        dst.write_bytes((FIXTURES_DIR / "zotero.sqlite").read_bytes())
        ft_dst = tmp_path / "fulltext.sqlite"
        ft_dst.write_bytes((FIXTURES_DIR / "fulltext.sqlite").read_bytes())
        conn = sqlite3.connect(dst)
        conn.execute("INSERT INTO items VALUES (20, 14, '2024-02-03', '2024-02-03', '2024-02-03', 1, 'ATCH020')")
        conn.execute("INSERT INTO itemAttachments VALUES (20, 2, 0, 'application/pdf', NULL, 'storage:bert.pdf')")
        conn.commit()
        conn.close()
        ft = sqlite3.connect(ft_dst)
        ft.execute("INSERT INTO fulltextContent (rowid, text) VALUES (20, 'a survey of transformer models')")
        ft.execute("INSERT INTO fulltextIndexState VALUES (20, 1)")
        ft.commit()
        ft.close()
        r = ZoteroReader(dst)
        yield r
        r.close()

    def test_more_fulltext_terms_ranks_higher(self, reader_two_pdfs):
        results = rank(reader_two_pdfs, "transformer attention mechanism", top_k=5)
        keys = [r["item"].key for r in results]
        assert keys[0] == "ATTN001"  # 3 fulltext terms vs 1 for BERT002
        assert "BERT002" in keys
