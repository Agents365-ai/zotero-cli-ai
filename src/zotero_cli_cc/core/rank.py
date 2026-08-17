"""Index-free ranked retrieval over Zotero's own full-text index.

Two-stage, no embeddings, no pre-built index:

- Stage 1 scores every item in scope with idf-weighted term coverage from
  Zotero's ``fulltextWords``/``fulltextItemWords`` tables (term frequencies
  are binary — Zotero stores unique (word, item) pairs — with document
  length normalisation via ``fulltextItems.indexedChars``), fused with a
  metadata LIKE ranking (title/abstract/creators/tags/notes) via RRF.
- Stage 2 (``build_ask_evidence``) re-ranks the top items by real term
  frequency from on-the-fly PDF text extraction (cached in PdfCache) and
  carves evidence passages around query-term hits.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from zotero_cli_cc.core.pdf_cache import PdfCache
from zotero_cli_cc.core.pdf_extractor import get_extractor

if TYPE_CHECKING:
    from zotero_cli_cc.core.reader import ZoteroReader
    from zotero_cli_cc.models import Collection, Item

# BM25 tuning (same constants the old chunk index used)
_K1 = 1.5
_B = 0.75
# Cap on PDFs extracted per ask call (first-N ranked items with a PDF)
_MAX_PDF_ITEMS = 5
_IN_BATCH = 900


def tokenize(text: str) -> list[str]:
    tokens = []
    for word in text.lower().split():
        word = re.sub(r"[.,;:!?()\"'\[\]{}]+$", "", word)
        word = re.sub(r"^[.,;:!?()\"'\[\]{}]+", "", word)
        if word:
            tokens.append(word)
    return tokens


def build_metadata_chunk(title: str, authors: str, abstract: str | None, tags: list[str]) -> str:
    parts = [f"Title: {title}", f"Authors: {authors}"]
    if abstract:
        parts.append(f"Abstract: {abstract}")
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")
    return "\n".join(parts)


def reciprocal_rank_fusion(*rankings: list[tuple[str, float]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse (id, score) rankings into one, sorted by fused score descending."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, (item_id, _score) in enumerate(ranking):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def extract_passages(text: str, terms: list[str], max_passages: int = 3, window: int = 300) -> list[str]:
    """Carve up to ``max_passages`` non-overlapping snippets around term hits."""
    if not text or not terms:
        return []
    lowered = text.lower()
    hits: list[int] = []
    for term in terms:
        start = 0
        for _ in range(3):  # up to 3 hit positions per term
            idx = lowered.find(term, start)
            if idx == -1:
                break
            hits.append(idx)
            start = idx + len(term)
    if not hits:
        return []
    passages: list[str] = []
    covered_end = -1
    for pos in sorted(hits):
        if pos < covered_end:
            continue
        start = max(0, pos - window)
        end = min(len(text), pos + window)
        if start > 0:
            space = text.find(" ", start)
            if 0 <= space < pos:
                start = space + 1
        if end < len(text):
            space = text.rfind(" ", pos, end)
            if space > pos:
                end = space
        passage = text[start:end].strip()
        if passage:
            passages.append(passage)
            covered_end = end
        if len(passages) >= max_passages:
            break
    return passages


def resolve_collection_key(reader: ZoteroReader, name_or_key: str) -> str | None:
    """Resolve a collection name or key to a collection key (recursive)."""
    collections = reader.get_collections()

    def _search(colls: list[Collection]) -> str | None:
        for c in colls:
            if c.key == name_or_key or c.name.lower() == name_or_key.lower():
                return c.key
            found = _search(c.children)
            if found:
                return found
        return None

    return _search(collections)


def convert_pdf_to_text(
    pdf_path: Path,
    extractor_name: str = "pdfium",
    progress_callback: Callable[[str, int, int, int], None] | None = None,
) -> str:
    """Extract PDF text with PdfCache (same path as the `pdf` command)."""
    cache = PdfCache()
    cached = cache.get(pdf_path, extractor_name)
    if cached is not None:
        return cached
    extractor = get_extractor(extractor_name)
    text = extractor.extract_text(pdf_path, progress_callback=progress_callback)  # type: ignore[call-arg]
    cache.put(pdf_path, extractor_name, text)
    return text


def _fulltext_scores(
    reader: ZoteroReader,
    terms: list[str],
    collection_key: str | None,
) -> dict[str, float]:
    """idf-weighted term coverage per parent item, from Zotero's full-text index.

    Zotero stores unique (wordID, itemID) pairs, so term frequency is binary;
    document length comes from fulltextItems.indexedChars. An item with
    several indexed attachments gets the max of its attachment scores.
    """
    candidates = reader.fulltext_candidates(collection_key)
    if not candidates:
        return {}
    att_to_parent: dict[int, str] = {}
    att_len: dict[int, int] = {}
    for parent_key, att_id, chars in candidates:
        att_to_parent[att_id] = parent_key
        att_len[att_id] = max(chars, 1)
    att_ids = sorted(att_to_parent)
    n_docs = len(att_ids)
    avg_dl = sum(att_len.values()) / n_docs

    conn = reader._connect()
    word_ids: dict[str, int] = {}
    for batch in _batches(terms):
        placeholders = ",".join("?" * len(batch))
        rows = conn.execute(
            f"SELECT wordID, word FROM fulltextWords WHERE word IN ({placeholders})",
            batch,
        ).fetchall()
        word_ids.update({r["word"]: r["wordID"] for r in rows})
    matched_ids = sorted(word_ids.values())
    if not matched_ids:
        return {}

    # Fetch matching (wordID, itemID) pairs once, then aggregate in Python:
    # df per term, and per-attachment idf sum with length normalisation.
    pairs: set[tuple[int, int]] = set()
    for w_batch in _batches(matched_ids):
        w_ph = ",".join("?" * len(w_batch))
        for a_batch in _batches(att_ids):
            a_ph = ",".join("?" * len(a_batch))
            rows = conn.execute(
                f"SELECT wordID, itemID FROM fulltextItemWords WHERE wordID IN ({w_ph}) AND itemID IN ({a_ph})",
                (*w_batch, *a_batch),
            ).fetchall()
            pairs.update((r["wordID"], r["itemID"]) for r in rows)

    df: dict[int, int] = {}
    for word_id, _item_id in pairs:
        df[word_id] = df.get(word_id, 0) + 1
    idf = {wid: math.log((n_docs - d + 0.5) / (d + 0.5) + 1) for wid, d in df.items()}

    att_score: dict[int, float] = {}
    for word_id, item_id in pairs:
        dl_norm = 1 - _B + _B * att_len[item_id] / avg_dl
        tf_factor = (_K1 + 1) / (1 + _K1 * dl_norm)  # tf = 1 (binary)
        att_score[item_id] = att_score.get(item_id, 0.0) + idf[word_id] * tf_factor

    scores: dict[str, float] = {}
    for att_id, score in att_score.items():
        parent = att_to_parent[att_id]
        scores[parent] = max(scores.get(parent, 0.0), score)
    return scores


def _metadata_scores(
    reader: ZoteroReader,
    terms: list[str],
    collection_key: str | None,
) -> dict[str, float]:
    """Count of distinct query terms matched per item across metadata fields."""
    conn = reader._connect()
    excl_sql, excl_params = reader._excluded_filter()
    # Strict per-library isolation (unlike reader.search, which keeps the
    # legacy no-filter behaviour for the user library): rank results must not
    # mix group-library items into a user-library query and vice versa.
    lib_sql, lib_params = "AND i.libraryID = ?", (reader._library_id,)
    col_sql = ""
    col_params: tuple = ()
    if collection_key is not None:
        col_row = conn.execute(
            "SELECT collectionID FROM collections WHERE libraryID = ? AND key = ?",
            (reader._library_id, collection_key),
        ).fetchone()
        if col_row is None:
            return {}
        col_sql = " AND i.itemID IN (SELECT itemID FROM collectionItems WHERE collectionID = ?)"
        col_params = (col_row["collectionID"],)

    hits: dict[int, set[str]] = {}
    for term in terms:
        pat = f"%{term}%"
        term_ids: set[int] = set()
        rows = conn.execute(
            "SELECT DISTINCT i.itemID, i.key FROM items i "
            "JOIN itemData id ON i.itemID = id.itemID "
            "JOIN itemDataValues iv ON id.valueID = iv.valueID "
            f"WHERE iv.value LIKE ? AND i.itemTypeID {excl_sql} {lib_sql}{col_sql}",
            (pat, *excl_params, *lib_params, *col_params),
        ).fetchall()
        term_ids.update(r["itemID"] for r in rows)
        rows = conn.execute(
            "SELECT DISTINCT ic.itemID FROM itemCreators ic "
            "JOIN creators c ON ic.creatorID = c.creatorID "
            "JOIN items i ON ic.itemID = i.itemID "
            f"WHERE (c.firstName LIKE ? OR c.lastName LIKE ?) AND i.itemTypeID {excl_sql} {lib_sql}{col_sql}",
            (pat, pat, *excl_params, *lib_params, *col_params),
        ).fetchall()
        term_ids.update(r["itemID"] for r in rows)
        rows = conn.execute(
            "SELECT DISTINCT it.itemID FROM itemTags it "
            "JOIN tags t ON it.tagID = t.tagID "
            "JOIN items i ON it.itemID = i.itemID "
            f"WHERE t.name LIKE ? AND i.itemTypeID {excl_sql} {lib_sql}{col_sql}",
            (pat, *excl_params, *lib_params, *col_params),
        ).fetchall()
        term_ids.update(r["itemID"] for r in rows)
        # Notes are child items — map back to the parent so note text scores
        # the paper it belongs to (top-level standalone notes are skipped).
        rows = conn.execute(
            "SELECT DISTINCT n.parentItemID AS itemID FROM itemNotes n "
            "JOIN items i ON n.parentItemID = i.itemID "
            f"WHERE n.note LIKE ? AND n.parentItemID IS NOT NULL "
            f"AND i.itemTypeID {excl_sql} {lib_sql}{col_sql}",
            (pat, *excl_params, *lib_params, *col_params),
        ).fetchall()
        term_ids.update(r["itemID"] for r in rows)
        for item_id in term_ids:
            hits.setdefault(item_id, set()).add(term)

    if not hits:
        return {}
    key_rows = conn.execute(
        f"SELECT itemID, key FROM items WHERE itemID IN ({','.join(str(i) for i in hits)})"
    ).fetchall()
    return {r["key"]: float(len(hits[r["itemID"]])) for r in key_rows}


def rank(
    reader: ZoteroReader,
    query: str,
    collection_key: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Fuse full-text and metadata rankings; return top-k scored items.

    Each result: {"item": Item, "score": float, "scores": {"rrf": float,
    "fulltext": float|None, "metadata": float|None}, "terms": list[str]}.
    """
    terms = sorted(set(tokenize(query)))
    if not terms:
        return []
    ft = _fulltext_scores(reader, terms, collection_key)
    md = _metadata_scores(reader, terms, collection_key)
    ft_ranking = sorted(ft.items(), key=lambda kv: kv[1], reverse=True)
    md_ranking = sorted(md.items(), key=lambda kv: kv[1], reverse=True)
    fused = reciprocal_rank_fusion(ft_ranking, md_ranking)

    results: list[dict] = []
    for key, score in fused[:top_k]:
        item = reader.get_item(key)
        if item is None:
            continue
        results.append(
            {
                "item": item,
                "score": round(score, 4),
                "scores": {
                    "rrf": round(score, 4),
                    "fulltext": round(ft[key], 4) if key in ft else None,
                    "metadata": round(md[key], 4) if key in md else None,
                },
                "terms": terms,
            }
        )
    return results


def build_ask_evidence(
    reader: ZoteroReader,
    ranked: list[dict],
    evidence_k: int = 12,
    max_pdf_items: int = _MAX_PDF_ITEMS,
    extractor_name: str = "pdfium",
) -> list[dict]:
    """Turn ranked items into a citation-keyed evidence list.

    Every ranked item contributes its metadata chunk; the first
    ``max_pdf_items`` items with an extractable PDF also contribute passages
    carved around query-term hits. zot does not run a generative LLM — the
    calling agent synthesizes and cites from this pack.
    """
    evidence: list[dict] = []
    pdf_items = 0
    for entry in ranked:
        item: Item = entry["item"]
        terms: list[str] = entry["terms"]
        scores = entry["scores"]
        authors = ", ".join(c.full_name for c in item.creators)
        evidence.append(
            {
                "cite_key": item.key,
                "source": "metadata",
                "text": build_metadata_chunk(item.title, authors, item.abstract, item.tags),
                "scores": scores,
            }
        )
        if pdf_items < max_pdf_items:
            attachment = reader.get_pdf_attachment(item.key)
            if attachment is not None and attachment.path is not None and attachment.path.exists():
                pdf_items += 1
                try:
                    text = convert_pdf_to_text(attachment.path, extractor_name)
                except Exception:
                    text = ""
                for passage in extract_passages(text, terms):
                    evidence.append(
                        {
                            "cite_key": item.key,
                            "source": "pdf",
                            "text": passage,
                            "scores": scores,
                        }
                    )
        if len(evidence) >= evidence_k:
            break
    return evidence[:evidence_k]


def _batches(ids: list, size: int = _IN_BATCH) -> Iterator[list]:
    for i in range(0, len(ids), size):
        yield ids[i : i + size]


def make_snippet(item: Item, terms: list[str], window: int = 220) -> str:
    """One-line preview for ranked results: a term-centred abstract excerpt."""
    abstract = item.abstract or ""
    passages = extract_passages(abstract, terms, max_passages=1, window=window)
    if passages:
        return passages[0]
    return abstract[:window].strip()
