"""MCP server exposing Zotero tools via FastMCP."""

from __future__ import annotations

import atexit
import logging
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from zotero_cli_cc.config import (
    get_data_dir,
    get_prefs_js_path,
    load_config,
    load_pdf_config,
)
from zotero_cli_cc.core.pdf_cache import PdfCache
from zotero_cli_cc.core.pdf_extractor import PdfExtractionError, get_extractor
from zotero_cli_cc.core.rank import build_ask_evidence, make_snippet, rank, resolve_collection_key
from zotero_cli_cc.core.reader import ZoteroReader
from zotero_cli_cc.core.writer import ZoteroWriteError, ZoteroWriter
from zotero_cli_cc.formatter import ANSWER_INSTRUCTIONS
from zotero_cli_cc.models import Collection, Item, Note

mcp = FastMCP("zotero", instructions="Read and write access to a local Zotero library")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_readers: dict[int, ZoteroReader] = {}
_writers: dict[str, ZoteroWriter] = {}
_log = logging.getLogger(__name__)


def _close_writers() -> None:
    for w in _writers.values():
        if hasattr(w, "_zot") and hasattr(w._zot, "client") and w._zot.client is not None:
            try:
                w._zot.client.close()
            except Exception:
                pass


atexit.register(_close_writers)


def _get_reader(library: str = "user") -> ZoteroReader:
    """Return a shared ZoteroReader, creating it on first use."""
    cfg = load_config()
    data_dir = get_data_dir(cfg)
    db_path = data_dir / "zotero.sqlite"
    prefs_path = get_prefs_js_path(cfg)

    library_id = 1
    if library.startswith("group:"):
        group_id = int(library[6:])
        temp = ZoteroReader(db_path, prefs_js_path=prefs_path)
        try:
            resolved = temp.resolve_group_library_id(group_id)
        finally:
            temp.close()
        if resolved is None:
            raise ValueError(f"Group '{group_id}' not found")
        library_id = resolved

    if library_id not in _readers:
        reader = ZoteroReader(db_path, library_id=library_id, prefs_js_path=prefs_path)
        _readers[library_id] = reader
        atexit.register(reader.close)
    return _readers[library_id]


def _get_writer(library: str = "user") -> ZoteroWriter:
    """Return a cached ZoteroWriter, creating it on first use.

    Raises ValueError if write credentials are not configured.
    """
    cache_key = library
    if cache_key not in _writers:
        cfg = load_config()
        if not cfg.has_write_credentials:
            raise ValueError("Write credentials not configured. Set library_id and api_key in your Zotero CLI config.")
        library_type = "user"
        lib_id = cfg.library_id
        if library.startswith("group:"):
            library_type = "group"
            lib_id = library[6:]
        _writers[cache_key] = ZoteroWriter(lib_id, cfg.api_key, library_type=library_type)
    return _writers[cache_key]


def _item_to_dict(item: Item, detail: str = "standard") -> dict:
    d: dict = {
        "key": item.key,
        "item_type": item.item_type,
        "title": item.title,
        "authors": [c.full_name for c in item.creators],
        "date": item.date,
    }
    if detail != "minimal":
        d["abstract"] = item.abstract
        d["url"] = item.url
        d["doi"] = item.doi
        d["tags"] = item.tags
        d["collections"] = item.collections
        d["date_added"] = item.date_added
        d["date_modified"] = item.date_modified
    if detail == "full":
        d["extra"] = item.extra
    return d


def _note_to_dict(note: Note) -> dict:
    return {
        "key": note.key,
        "parent_key": note.parent_key,
        "content": note.content,
        "tags": note.tags,
    }


def _collection_to_dict(coll: Collection) -> dict:
    return {
        "key": coll.key,
        "name": coll.name,
        "parent_key": coll.parent_key,
        "children": [_collection_to_dict(c) for c in coll.children],
    }


# ---------------------------------------------------------------------------
# Handler functions (testable without MCP decorator)
# ---------------------------------------------------------------------------


def _handle_search(
    query: str,
    collection: str | None,
    limit: int,
    item_type: str | None = None,
    sort: str | None = None,
    direction: str = "desc",
    library: str = "user",
) -> dict:
    reader = _get_reader(library)
    result = reader.search(
        query, collection=collection, item_type=item_type, sort=sort, direction=direction, limit=limit
    )
    return {
        "items": [_item_to_dict(i) for i in result.items],
        "total": result.total,
        "query": result.query,
    }


def _handle_list_items(
    limit: int,
    item_type: str | None = None,
    sort: str | None = None,
    direction: str = "desc",
    library: str = "user",
) -> dict:
    reader = _get_reader(library)
    result = reader.search("", collection=None, item_type=item_type, sort=sort, direction=direction, limit=limit)
    return {
        "items": [_item_to_dict(i) for i in result.items],
        "total": result.total,
    }


def _handle_read(key: str, detail: str = "standard", library: str = "user") -> dict:
    reader = _get_reader(library)
    item = reader.get_item(key)
    if item is None:
        raise ValueError(f"Item '{key}' not found")
    notes = reader.get_notes(key)
    return {
        "item": _item_to_dict(item, detail=detail),
        "notes": [_note_to_dict(n) for n in notes],
    }


def _handle_pdf(key: str, pages: str | None, library: str = "user") -> dict:
    reader = _get_reader(library)
    att = reader.get_pdf_attachment(key)
    if att is None:
        raise ValueError(f"No PDF attachment found for item '{key}'")
    pdf_path = att.path
    if not pdf_path or not pdf_path.exists():
        raise ValueError(f"PDF file not found at {pdf_path or att.filename}")

    page_range = None
    if pages:
        parts = pages.split("-")
        start = int(parts[0])
        end = int(parts[1]) if len(parts) > 1 else start
        page_range = (start, end)

    extractor_name = load_pdf_config().extractor
    pdf_extractor = get_extractor(extractor_name)
    cache = PdfCache()
    try:
        if page_range is None:
            cached = cache.get(pdf_path, extractor_name)
            if cached is not None:
                text = cached
            else:
                text = pdf_extractor.extract_text(pdf_path)
                cache.put(pdf_path, extractor_name, text)
        else:
            text = pdf_extractor.extract_text(pdf_path, pages=page_range)
    except PdfExtractionError as e:
        if extractor_name == "mineru":
            pdf_extractor = get_extractor("pdfium")
            try:
                if page_range is None:
                    text = pdf_extractor.extract_text(pdf_path)
                    cache.put(pdf_path, "pdfium", text)
                else:
                    text = pdf_extractor.extract_text(pdf_path, pages=page_range)
            except PdfExtractionError as e2:
                return {"error": str(e2), "context": "pdf"}
        else:
            return {"error": str(e), "context": "pdf"}
    finally:
        cache.close()

    return {"key": key, "pages": pages, "text": text}


def _handle_annotations(key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    att = reader.get_pdf_attachment(key)
    if att is None:
        return {"error": f"No PDF attachment found for '{key}'"}
    pdf_path = att.path
    if not pdf_path or not pdf_path.exists():
        return {"error": f"PDF file not found at {pdf_path or att.filename}"}
    # Annotation extraction is a pymupdf-only capability.
    annots = get_extractor("pymupdf").extract_annotations(pdf_path)
    return {"key": key, "annotations": annots, "total": len(annots)}


def _handle_references(key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    att = reader.get_pdf_attachment(key)
    if att is None:
        return {"error": f"No PDF attachment found for '{key}'"}
    pdf_path = att.path
    if not pdf_path or not pdf_path.exists():
        return {"error": f"PDF file not found at {pdf_path or att.filename}"}
    try:
        refs = get_extractor("grobid").extract_references(pdf_path)
    except PdfExtractionError as e:
        return {
            "error": str(e),
            "context": "references",
            "hint": "Reference parsing needs a running GROBID service "
            "(default http://localhost:8070; set pdf.grobid_url or ZOT_GROBID_URL)",
        }
    return {"key": key, "references": refs, "total": len(refs)}


def _handle_tables(key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    att = reader.get_pdf_attachment(key)
    if att is None:
        return {"error": f"No PDF attachment found for '{key}'"}
    pdf_path = att.path
    if not pdf_path or not pdf_path.exists():
        return {"error": f"PDF file not found at {pdf_path or att.filename}"}
    try:
        tables = get_extractor("pdfplumber").extract_tables(pdf_path)
    except PdfExtractionError as e:
        return {
            "error": str(e),
            "context": "tables",
            "hint": "Install the pdfplumber extra: pip install 'zotero-cli-ai[pdfplumber]'",
        }
    return {"key": key, "tables": tables, "total": len(tables)}


def _handle_summarize(key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    item = reader.get_item(key)
    if item is None:
        raise ValueError(f"Item '{key}' not found")
    notes = reader.get_notes(key)
    return {
        "title": item.title,
        "authors": [c.full_name for c in item.creators],
        "year": item.date,
        "doi": item.doi,
        "abstract": item.abstract,
        "tags": item.tags,
        "notes": [n.content[:500] for n in notes],
    }


def _handle_summarize_all(limit: int, library: str = "user") -> dict:
    reader = _get_reader(library)
    result = reader.search("", limit=limit)
    items = []
    for item in result.items:
        items.append(
            {
                "key": item.key,
                "title": item.title,
                "authors": [c.full_name for c in item.creators],
                "abstract": item.abstract,
                "tags": item.tags,
                "date": item.date,
            }
        )
    return {"items": items, "total": result.total}


def _handle_export(key: str, fmt: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    citation = reader.export_citation(key, fmt=fmt)
    if citation is None:
        raise ValueError(f"Item '{key}' not found or format '{fmt}' not supported")
    return {
        "citation": citation,
        "format": fmt,
        "key": key,
    }


def _handle_relate(key: str, limit: int, library: str = "user") -> dict:
    reader = _get_reader(library)
    items = reader.get_related_items(key, limit=limit)
    return {
        "items": [_item_to_dict(i) for i in items],
        "source_key": key,
    }


def _handle_recent(days: int, modified: bool, limit: int, library: str = "user") -> dict:
    from datetime import timedelta

    reader = _get_reader(library)
    sort_field = "dateModified" if modified else "dateAdded"
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_str = since.strftime("%Y-%m-%d %H:%M:%S")
    items = reader.get_recent_items(since=since_str, sort=sort_field, limit=limit)
    return {"items": [_item_to_dict(i) for i in items], "total": len(items)}


def _handle_find_orphans(dead_only: bool = False, library: str = "user") -> dict:
    import dataclasses

    reader = _get_reader(library)
    orphans = reader.find_orphan_attachments()
    if dead_only:
        orphans = [o for o in orphans if o.classification == "dead"]
    counts = {"dead": 0, "recoverable": 0, "unknown": 0}
    for o in orphans:
        counts[o.classification] = counts.get(o.classification, 0) + 1
    return {"orphans": [dataclasses.asdict(o) for o in orphans], "total": len(orphans), "counts": counts}


def _handle_note_view(key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    notes = reader.get_notes(key)
    return {
        "notes": [_note_to_dict(n) for n in notes],
        "parent_key": key,
    }


def _handle_tag_view(key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    item = reader.get_item(key)
    if item is None:
        raise ValueError(f"Item '{key}' not found")
    return {
        "tags": item.tags,
        "key": key,
        "title": item.title,
    }


def _handle_collection_list(library: str = "user") -> dict:
    reader = _get_reader(library)
    collections = reader.get_collections()
    return {
        "collections": [_collection_to_dict(c) for c in collections],
    }


def _handle_collection_items(collection_key: str, library: str = "user") -> dict:
    reader = _get_reader(library)
    items = reader.get_collection_items(collection_key)
    return {
        "items": [_item_to_dict(i) for i in items],
        "collection_key": collection_key,
    }


def _handle_duplicates(strategy: str = "both", threshold: float = 0.85, limit: int = 50, library: str = "user") -> dict:
    reader = _get_reader(library)
    groups = reader.find_duplicates(strategy=strategy, threshold=threshold, limit=limit)
    result_groups = []
    for g in groups:
        result_groups.append(
            {
                "match_type": g.match_type,
                "score": g.score,
                "items": [_item_to_dict(i) for i in g.items],
            }
        )
    return {"groups": result_groups, "total": len(result_groups)}


# ---------------------------------------------------------------------------
# Write handler functions
# ---------------------------------------------------------------------------


def _handle_note_add(key: str, content: str, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        note_key = writer.add_note(key, content)
        return {"note_key": note_key}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "note_add"}


def _handle_note_update(note_key: str, content: str, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        writer.update_note(note_key, content)
        return {"note_key": note_key, "updated": True}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "note_update"}


def _handle_tag_add(keys: list[str], tags: list[str], library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
    except (ValueError, ZoteroWriteError) as e:
        return {"error": str(e), "context": "tag_add"}
    results = []
    for key in keys:
        try:
            writer.add_tags(key, tags)
            results.append({"key": key, "tags_added": tags})
        except ZoteroWriteError as e:
            results.append({"key": key, "error": str(e)})
    return {"results": results}


def _handle_tag_remove(keys: list[str], tags: list[str], library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
    except (ValueError, ZoteroWriteError) as e:
        return {"error": str(e), "context": "tag_remove"}
    results = []
    for key in keys:
        try:
            writer.remove_tags(key, tags)
            results.append({"key": key, "tags_removed": tags})
        except ZoteroWriteError as e:
            results.append({"key": key, "error": str(e)})
    return {"results": results}


def _handle_add(doi: str | None, url: str | None, library: str = "user") -> dict:
    if not doi and not url:
        raise ValueError("Either doi or url must be provided.")
    from zotero_cli_cc.core.metadata_resolver import MetadataResolveError, resolve_doi

    extra_fields: dict | None = None
    resolve_warning: str | None = None
    if doi:
        try:
            extra_fields = resolve_doi(doi)
            if extra_fields is None:
                resolve_warning = "no_match"
        except MetadataResolveError as e:
            resolve_warning = str(e)
    try:
        writer = _get_writer(library)
        item_key = writer.add_item(doi=doi, url=url, extra_fields=extra_fields)
        result: dict = {"item_key": item_key}
        if extra_fields:
            result["resolved"] = {k: v for k, v in extra_fields.items() if k in {"title", "publicationTitle", "date"}}
        elif doi:
            result["resolve_warning"] = resolve_warning
        return result
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "add"}


def _handle_delete(keys: list[str], library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
    except (ValueError, ZoteroWriteError) as e:
        return {"error": str(e), "context": "delete"}
    results = []
    for key in keys:
        try:
            writer.delete_item(key)
            results.append({"key": key, "deleted": True})
        except ZoteroWriteError as e:
            results.append({"key": key, "deleted": False, "error": str(e)})
    return {"results": results}


def _handle_update(key: str, fields: dict, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        writer.update_item(key, fields)
        return {"status": "updated", "key": key, "fields": fields}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "update"}


def _handle_collection_create(name: str, parent_key: str | None, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        collection_key = writer.create_collection(name, parent_key=parent_key)
        return {"collection_key": collection_key}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "collection_create"}


def _handle_collection_move(item_key: str, collection_key: str, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        writer.move_to_collection(item_key, collection_key)
        return {"item_key": item_key, "collection_key": collection_key}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "collection_move"}


def _handle_collection_delete(collection_key: str, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        writer.delete_collection(collection_key)
        return {"deleted": True, "collection_key": collection_key}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "collection_delete"}


def _handle_collection_reorganize(plan: dict, library: str = "user") -> dict:
    """Execute a collection reorganization plan."""
    try:
        writer = _get_writer(library)
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "collection_reorganize"}

    collections = plan.get("collections", [])
    if not collections:
        raise ValueError("No collections in plan.")

    created: dict[str, str] = {}  # name -> key
    results = []

    for coll in collections:
        name = coll["name"]
        parent_name = coll.get("parent")
        parent_key = created.get(parent_name) if parent_name else None
        items = coll.get("items", [])

        try:
            col_key = writer.create_collection(name, parent_key=parent_key)
            created[name] = col_key

            moved = []
            failed = []
            for item_key in items:
                try:
                    writer.move_to_collection(item_key, col_key)
                    moved.append(item_key)
                except ZoteroWriteError as e:
                    failed.append({"key": item_key, "error": str(e)})

            results.append(
                {
                    "name": name,
                    "collection_key": col_key,
                    "items_moved": len(moved),
                    "items_failed": len(failed),
                    "failures": failed,
                }
            )
        except ZoteroWriteError as e:
            results.append({"name": name, "error": str(e)})

    return {"collections_created": len(created), "results": results}


def _handle_collection_rename(collection_key: str, new_name: str, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        writer.rename_collection(collection_key, new_name)
        return {"collection_key": collection_key, "new_name": new_name}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "collection_rename"}


def _handle_trash_list(limit: int = 50, library: str = "user") -> dict:
    reader = _get_reader(library)
    items = reader.get_trash_items(limit=limit)
    return {"items": [_item_to_dict(i) for i in items], "total": len(items)}


def _handle_trash_restore(key: str, library: str = "user") -> dict:
    try:
        writer = _get_writer(library)
        writer.restore_from_trash(key)
        return {"key": key, "restored": True}
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "trash_restore"}


def _handle_attach(parent_key: str, file_path: str, library: str = "user", via_bridge: bool | None = None) -> dict:
    from zotero_cli_cc.core.local_bridge import resolve_use_bridge

    if resolve_use_bridge(via_bridge):
        from zotero_cli_cc.core.local_bridge import LocalBridgeError, ensure_group_import_supported, import_file

        fp = Path(file_path)
        group_id = int(library.split(":", 1)[1]) if library.startswith("group:") else None
        try:
            if group_id is not None:
                ensure_group_import_supported()
            result = import_file(parent_key, str(fp.resolve()), title=fp.name, group_id=group_id)
        except LocalBridgeError as e:
            return {"error": str(e), "context": "attach", "code": e.code}
        return {
            "key": result.get("attachment_key"),
            "parent_key": parent_key,
            "filename": result.get("filename") or fp.name,
            "stored": "local",
        }
    try:
        writer = _get_writer(library)
        att_key, upload_result = writer.upload_attachment(parent_key, Path(file_path))
        return {
            "key": att_key,
            "parent_key": parent_key,
            "filename": Path(file_path).name,
            "stored": "cloud",
            "result": upload_result,
        }
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "attach"}


def _handle_add_from_pdf(file_path: str, doi_override: str | None = None, library: str = "user") -> dict:
    from zotero_cli_cc.core.metadata_resolver import MetadataResolveError, resolve_doi

    doi = doi_override
    if not doi:
        doi = get_extractor("pymupdf").extract_doi(Path(file_path))
    if not doi:
        return {"error": "No DOI found in PDF. Use doi_override to specify manually."}

    extra_fields: dict | None = None
    try:
        extra_fields = resolve_doi(doi)
    except MetadataResolveError:
        extra_fields = None

    try:
        writer = _get_writer(library)
        item_key = writer.add_item(doi=doi, extra_fields=extra_fields)
    except ZoteroWriteError as e:
        return {"error": str(e), "context": "add_from_pdf"}

    try:
        att_key, _ = writer.upload_attachment(item_key, Path(file_path))
        result: dict = {
            "item_key": item_key,
            "attachment_key": att_key,
            "doi": doi,
        }
        if extra_fields:
            result["resolved"] = {k: v for k, v in extra_fields.items() if k in {"title", "publicationTitle", "date"}}
        else:
            result["note"] = "Crossref had no metadata for this DOI; item created with DOI only."
        return result
    except ZoteroWriteError as e:
        return {
            "item_key": item_key,
            "doi": doi,
            "error": f"Attachment upload failed: {e}. Retry with: attach(parent_key='{item_key}', file_path='{file_path}')",
        }


# ---------------------------------------------------------------------------
# Workspace / ask handlers (index-free, collection-backed)
# ---------------------------------------------------------------------------


def _handle_workspace_query(question: str, workspace: str | None = None, top_k: int = 5, library: str = "user") -> dict:
    reader = _get_reader(library)
    collection_key = None
    if workspace:
        collection_key = resolve_collection_key(reader, workspace)
        if collection_key is None:
            return {"error": f"Collection '{workspace}' not found. Use collection_list to see available collections."}
    results = rank(reader, question, collection_key=collection_key, top_k=top_k)
    return {
        "query": question,
        "workspace": workspace,
        "results": [
            {
                "rank": i + 1,
                "score": r["score"],
                "scores": r["scores"],
                "item_key": r["item"].key,
                "title": r["item"].title,
                "creators": [c.full_name for c in r["item"].creators],
                "date": r["item"].date,
                "snippet": make_snippet(r["item"], r["terms"]),
            }
            for i, r in enumerate(results)
        ],
    }


def _handle_ask(question: str, workspace: str | None = None, evidence_k: int = 12, library: str = "user") -> dict:
    reader = _get_reader(library)
    collection_key = None
    if workspace:
        collection_key = resolve_collection_key(reader, workspace)
        if collection_key is None:
            return {"error": f"Collection '{workspace}' not found. Use collection_list to see available collections."}
    ranked = rank(reader, question, collection_key=collection_key, top_k=evidence_k)
    evidence = build_ask_evidence(reader, ranked, evidence_k=evidence_k)
    return {
        "question": question,
        "workspace": workspace,
        "mode": "index-free",
        "evidence": evidence,
        "answer_instructions": ANSWER_INSTRUCTIONS,
    }


# ---------------------------------------------------------------------------
# Utility handler functions (cite, stats, update_status)
# ---------------------------------------------------------------------------


def _handle_cite(key: str, style: str = "apa", library: str = "user") -> dict:
    from zotero_cli_cc.commands.cite import STYLES

    reader = _get_reader(library)
    item = reader.get_item(key)
    if item is None:
        return {"error": f"Item '{key}' not found."}
    if style not in STYLES:
        return {"error": f"Unknown style '{style}'. Use 'apa', 'nature', or 'vancouver'."}
    formatter = STYLES[style]
    citation = formatter(item)
    return {"citation": citation, "style": style, "key": key}


def _handle_stats(library: str = "user") -> dict:
    reader = _get_reader(library)
    return reader.get_stats()


def _handle_update_status(
    key: str | None = None,
    collection: str | None = None,
    limit: int = 50,
    apply: bool = False,
    library: str = "user",
) -> dict:
    import os

    from zotero_cli_cc.core.semantic_scholar import SemanticScholarClient, extract_preprint_info

    cfg = load_config()
    reader = _get_reader(library)

    if key:
        item = reader.get_item(key)
        if not item:
            return {"error": f"Item '{key}' not found."}
        items = [item]
    else:
        items = reader.get_arxiv_preprints(collection=collection, limit=limit)

    if not items:
        return {"results": [], "published": 0, "checked": 0}

    preprint_items = []
    for item in items:
        info = extract_preprint_info(
            url=item.url,
            doi=item.doi,
            extra=item.extra.get("extra") if item.extra else None,
        )
        if info:
            preprint_items.append((item.key, info, item.title))

    if not preprint_items:
        return {"results": [], "published": 0, "checked": 0}

    api_key = (
        os.environ.get("S2_API_KEY", "")
        or os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
        or cfg.semantic_scholar_api_key
    )
    client = SemanticScholarClient(api_key=api_key or None)
    results = []
    published_count = 0

    try:
        for item_key, info, title in preprint_items:
            status = client.check_publication(info)
            if status and status.is_published:
                published_count += 1
                results.append(
                    {
                        "key": item_key,
                        "title": title,
                        "published": True,
                        "venue": status.venue,
                        "journal": status.journal_name,
                        "doi": status.doi,
                        "date": status.publication_date,
                    }
                )
            else:
                results.append(
                    {
                        "key": item_key,
                        "title": title,
                        "published": False,
                    }
                )
    finally:
        client.close()

    if apply and published_count > 0:
        try:
            writer = _get_writer(library)
        except ValueError:
            return {
                "results": results,
                "published": published_count,
                "checked": len(preprint_items),
                "error": "Write credentials not configured. Cannot apply updates.",
            }
        updated = 0
        for r in results:
            if not r["published"]:
                continue
            fields: dict[str, str] = {}
            if r.get("doi"):
                fields["DOI"] = str(r["doi"])
            if r.get("venue"):
                fields["publicationTitle"] = str(r["venue"])
            elif r.get("journal"):
                fields["publicationTitle"] = str(r["journal"])
            if r.get("date"):
                fields["date"] = str(r["date"])
            if fields:
                try:
                    writer.update_item(str(r["key"]), fields)
                    r["updated"] = True
                    updated += 1
                except ZoteroWriteError as e:
                    r["update_error"] = str(e)
        return {"results": results, "published": published_count, "checked": len(preprint_items), "updated": updated}

    return {"results": results, "published": published_count, "checked": len(preprint_items)}


# ---------------------------------------------------------------------------
# MCP tool definitions
# ---------------------------------------------------------------------------


@mcp.tool()
def search(
    query: str,
    collection: str | None = None,
    item_type: str | None = None,
    sort: str | None = None,
    direction: str = "desc",
    limit: int = 50,
    library: str = "user",
) -> dict:
    """Search the Zotero library by title, author, tag, or full text.

    Args:
        query: Search query string.
        collection: Optional collection name or key to filter results.
        item_type: Optional item type filter (e.g. journalArticle, book, preprint).
        sort: Sort field — 'dateAdded', 'dateModified', 'title', or 'creator'.
        direction: Sort direction — 'asc' or 'desc' (default 'desc').
        limit: Maximum number of results (default 50).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_search(
        query, collection, limit, item_type=item_type, sort=sort, direction=direction, library=library
    )


@mcp.tool()
def list_items(
    item_type: str | None = None,
    sort: str | None = None,
    direction: str = "desc",
    limit: int = 50,
    library: str = "user",
) -> dict:
    """List all items in the Zotero library.

    Args:
        item_type: Optional item type filter (e.g. journalArticle, book, preprint).
        sort: Sort field — 'dateAdded', 'dateModified', 'title', or 'creator'.
        direction: Sort direction — 'asc' or 'desc' (default 'desc').
        limit: Maximum number of items to return (default 50).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_list_items(limit, item_type=item_type, sort=sort, direction=direction, library=library)


@mcp.tool()
def read(key: str, detail: str = "standard", library: str = "user") -> dict:
    """Read full details of a Zotero item including its notes.

    Args:
        key: The Zotero item key (e.g. 'ABC123').
        detail: Detail level — 'minimal', 'standard', or 'full'.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_read(key, detail, library=library)


@mcp.tool()
def pdf(key: str, pages: str | None = None, library: str = "user") -> dict:
    """Extract text from the PDF attachment of a Zotero item.

    Args:
        key: The Zotero item key.
        pages: Optional page range (e.g. '1-5' or '3' for a single page).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_pdf(key, pages, library=library)


@mcp.tool()  # type: ignore[no-redef]
def annotations(key: str, library: str = "user") -> dict:
    """Extract annotations (highlights, notes, comments) from a PDF attachment.

    Args:
        key: Item key whose PDF attachment to extract annotations from.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_annotations(key, library=library)


@mcp.tool()
def references(key: str, library: str = "user") -> dict:
    """Extract the parsed reference list (bibliography) from a PDF attachment.

    Returns each reference's title, authors, year, journal, and DOI. Requires a
    running GROBID service (configured via pdf.grobid_url / ZOT_GROBID_URL); the
    response carries an 'error' + 'hint' if it is unreachable. Useful for
    citation verification and detecting fabricated references.

    Args:
        key: Item key whose PDF attachment to parse references from.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_references(key, library=library)


@mcp.tool()
def tables(key: str, library: str = "user") -> dict:
    """Extract tables from a PDF attachment (pure-Python pdfplumber, no network).

    Returns a list of tables, each with its page number and rows (list of string
    cells). Requires the optional pdfplumber extractor; the response carries an
    'error' + 'hint' if it is not installed.

    Args:
        key: Item key whose PDF attachment to extract tables from.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_tables(key, library=library)


@mcp.tool()
def summarize(key: str, library: str = "user") -> dict:
    """Get a structured summary of a Zotero item for AI consumption.

    Args:
        key: The Zotero item key.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_summarize(key, library=library)


@mcp.tool()
def summarize_all(limit: int = 10000, library: str = "user") -> dict:
    """Export all items with key, title, abstract, authors, tags for AI classification.

    Args:
        limit: Maximum number of items (default 10000).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_summarize_all(limit, library=library)


@mcp.tool()
def export(key: str, fmt: str = "bibtex", library: str = "user") -> dict:
    """Export citation for a Zotero item.

    Args:
        key: The Zotero item key.
        fmt: Citation format — 'bibtex', 'csl-json', or 'ris' (default 'bibtex').
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_export(key, fmt, library=library)


@mcp.tool()
def relate(key: str, limit: int = 20, library: str = "user") -> dict:
    """Find items related to a given Zotero item.

    Args:
        key: The Zotero item key.
        limit: Maximum number of related items (default 20).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_relate(key, limit, library=library)


@mcp.tool()
def recent(days: int = 7, modified: bool = False, limit: int = 50, library: str = "user") -> dict:
    """Show recently added or modified items.

    Args:
        days: Number of days to look back (default: 7)
        modified: If True, use dateModified instead of dateAdded
        limit: Maximum number of items to return
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_recent(days, modified, limit, library=library)


@mcp.tool()
def note_view(key: str, library: str = "user") -> dict:
    """View all notes attached to a Zotero item.

    Args:
        key: The Zotero item key.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_note_view(key, library=library)


@mcp.tool()
def tag_view(key: str, library: str = "user") -> dict:
    """View tags for a Zotero item.

    Args:
        key: The Zotero item key.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_tag_view(key, library=library)


@mcp.tool()
def collection_list(library: str = "user") -> dict:
    """List all collections in the Zotero library.

    Args:
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_list(library=library)


@mcp.tool()
def collection_items(collection_key: str, library: str = "user") -> dict:
    """List all items in a specific Zotero collection.

    Args:
        collection_key: The collection key.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_items(collection_key, library=library)


@mcp.tool()
def duplicates(strategy: str = "both", threshold: float = 0.85, limit: int = 50, library: str = "user") -> dict:
    """Find potential duplicate items by DOI and/or title similarity.

    Args:
        strategy: Detection strategy — 'doi', 'title', or 'both' (default 'both').
        threshold: Minimum title similarity ratio (0.0–1.0, default 0.85).
        limit: Maximum number of duplicate groups to return (default 50).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_duplicates(strategy, threshold, limit, library=library)


# ---------------------------------------------------------------------------
# Write tools
# ---------------------------------------------------------------------------


@mcp.tool()
def note_add(key: str, content: str, library: str = "user") -> dict:
    """Add a note to a Zotero item.

    Args:
        key: The Zotero item key to attach the note to.
        content: The note content (HTML or plain text).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_note_add(key, content, library=library)


@mcp.tool()
def note_update(note_key: str, content: str, library: str = "user") -> dict:
    """Update an existing note in the Zotero library.

    Args:
        note_key: The Zotero note key to update.
        content: The new note content (HTML or plain text).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_note_update(note_key, content, library=library)


@mcp.tool()
def tag_add(keys: list[str], tags: list[str], library: str = "user") -> dict:
    """Add tags to one or more Zotero items.

    Args:
        keys: List of Zotero item keys (e.g. ['ABC123'] or ['K1', 'K2', 'K3']).
        tags: List of tag strings to add.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_tag_add(keys, tags, library=library)


@mcp.tool()
def tag_remove(keys: list[str], tags: list[str], library: str = "user") -> dict:
    """Remove tags from one or more Zotero items.

    Args:
        keys: List of Zotero item keys (e.g. ['ABC123'] or ['K1', 'K2', 'K3']).
        tags: List of tag strings to remove.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_tag_remove(keys, tags, library=library)


@mcp.tool()
def add(doi: str | None = None, url: str | None = None, library: str = "user") -> dict:
    """Add a new item to the Zotero library by DOI or URL.

    Args:
        doi: The DOI of the item (e.g. '10.1234/test').
        url: The URL of the item.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_add(doi, url, library=library)


@mcp.tool()
def delete(keys: list[str], library: str = "user") -> dict:
    """Delete one or more items from the Zotero library (move to trash).

    Args:
        keys: List of Zotero item keys to delete (e.g. ['ABC123'] or ['K1', 'K2']).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_delete(keys, library=library)


@mcp.tool()
def update(
    key: str, title: str | None = None, date: str | None = None, fields: dict | None = None, library: str = "user"
) -> dict:
    """Update item metadata. Pass title/date directly or use fields dict for arbitrary fields.

    Args:
        key: Item key to update.
        title: New title (optional).
        date: New date (optional).
        fields: Dict of field_name: value pairs for arbitrary fields (optional).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    update_fields: dict[str, str] = {}
    if title:
        update_fields["title"] = title
    if date:
        update_fields["date"] = date
    if fields:
        update_fields.update(fields)
    if not update_fields:
        return {"error": "No fields to update"}
    return _handle_update(key, update_fields, library=library)


@mcp.tool()
def collection_create(name: str, parent_key: str | None = None, library: str = "user") -> dict:
    """Create a new collection in the Zotero library.

    Args:
        name: The name for the new collection.
        parent_key: Optional parent collection key for creating a subcollection.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_create(name, parent_key, library=library)


@mcp.tool()
def collection_move(item_key: str, collection_key: str, library: str = "user") -> dict:
    """Move an item to a collection. Requires API credentials.

    Args:
        item_key: The Zotero item key.
        collection_key: The target collection key.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_move(item_key, collection_key, library=library)


@mcp.tool()
def collection_delete(collection_key: str, library: str = "user") -> dict:
    """Delete a collection from the Zotero library. Requires API credentials.

    Args:
        collection_key: The collection key to delete.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_delete(collection_key, library=library)


@mcp.tool()
def collection_rename(collection_key: str, new_name: str, library: str = "user") -> dict:
    """Rename a collection in the Zotero library. Requires API credentials.

    Args:
        collection_key: The collection key to rename.
        new_name: The new name for the collection.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_rename(collection_key, new_name, library=library)


@mcp.tool()
def collection_reorganize(plan: dict, library: str = "user") -> dict:
    """Batch create collections and move items based on a reorganization plan.

    The plan should have this structure:
    {"collections": [{"name": "Topic", "items": ["KEY1", "KEY2"]}, ...]}

    Optional "parent" field creates subcollections under an already-created collection.
    Requires API credentials.

    Args:
        plan: JSON object with collections array, each having name and items list.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_collection_reorganize(plan, library=library)


@mcp.tool()
def trash_list(limit: int = 50, library: str = "user") -> dict:
    """List items currently in the Zotero trash.

    Args:
        limit: Maximum number of trashed items to return (default 50).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_trash_list(limit, library=library)


@mcp.tool()
def trash_restore(key: str, library: str = "user") -> dict:
    """Restore a trashed item back to the Zotero library.

    Args:
        key: The item key to restore from trash.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_trash_restore(key, library=library)


@mcp.tool()
def attach(parent_key: str, file_path: str, library: str = "user", via_bridge: bool | None = None) -> dict:
    """Upload a file attachment to an existing Zotero item.

    The Web-API path uploads into zotero.org cloud storage, which only reaches the
    local storage/ folder after a desktop file-sync. The bridge path imports through
    the running Zotero desktop (zot-cli-bridge plugin) so the file lands in local
    storage immediately and cooperates with attachment-moving plugins.

    The route is auto-detected by default (via_bridge=None): the bridge is used when
    the desktop is reachable, else the Web API. Returns 'stored' as 'local' (bridge)
    or 'cloud' (Web API); cloud results also report 'result' as 'created' or 'exists'.

    Args:
        parent_key: The item key to attach the file to.
        file_path: Path to the file to upload.
        library: Library — 'user' (default) or 'group:<id>'.
        via_bridge: True forces the desktop bridge, False forces the Web API,
            None (default) auto-detects a running bridge.
    """
    return _handle_attach(parent_key, file_path, library=library, via_bridge=via_bridge)


@mcp.tool()
def find_orphans(dead_only: bool = False, library: str = "user") -> dict:
    """Find storage-backed attachments whose file is missing from local storage.

    These show "the attached file could not be found" in Zotero — usually a
    Web-API upload that landed the file in cloud storage only. Each is
    classified: 'dead' (no copy anywhere — safe to delete with the `delete`
    tool), 'recoverable' (server still has it — run a Zotero file-sync), or
    'unknown'. Read-only; pair with `delete` to clean up the dead ones.

    Args:
        dead_only: Only return 'dead' orphans (no copy anywhere).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_find_orphans(dead_only=dead_only, library=library)


@mcp.tool()
def add_from_pdf(file_path: str, doi_override: str | None = None, library: str = "user") -> dict:
    """Add an item from a local PDF by extracting its DOI, then attach the PDF.

    Note: The Zotero Web API creates bare items (DOI only). Sync with Zotero desktop
    to retrieve full metadata (title, authors, etc.).

    Args:
        file_path: Path to the PDF file.
        doi_override: Optional DOI to use instead of extracting from PDF.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_add_from_pdf(file_path, doi_override, library=library)


# ---------------------------------------------------------------------------
# Workspace tools (index-free; a workspace is a Zotero collection)
# ---------------------------------------------------------------------------


@mcp.tool()
def workspace_query(question: str, workspace: str | None = None, top_k: int = 5, library: str = "user") -> dict:
    """Rank papers by relevance to a natural-language question.

    Index-free retrieval over Zotero's own full-text index plus metadata,
    fused with RRF. Always fresh — there is no index to build. A workspace
    is simply a Zotero collection; manage membership in the Zotero app or
    via the collection_* tools.

    Args:
        question: Natural language query.
        workspace: Optional collection name or key to scope the search
            (default: whole library).
        top_k: Number of results to return (default 5).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_workspace_query(question, workspace=workspace, top_k=top_k, library=library)


@mcp.tool()
def ask(question: str, workspace: str | None = None, evidence_k: int = 12, library: str = "user") -> dict:
    """Retrieve a citation-keyed evidence pack to answer a question.

    Returns evidence entries tagged with Zotero item keys (cite_key) plus
    answer_instructions. zot does not call an LLM — synthesize and cite the
    answer from the evidence yourself.

    Args:
        question: Natural language question.
        workspace: Optional collection name or key to scope retrieval
            (default: whole library).
        evidence_k: Number of evidence entries to return (default 12).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_ask(question, workspace=workspace, evidence_k=evidence_k, library=library)


# ---------------------------------------------------------------------------
# Utility tools
# ---------------------------------------------------------------------------


@mcp.tool()
def cite(key: str, style: str = "apa", library: str = "user") -> dict:
    """Format a citation for a Zotero item in APA, Nature, or Vancouver style.

    Args:
        key: The Zotero item key.
        style: Citation style — 'apa' (default), 'nature', or 'vancouver'.
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_cite(key, style, library=library)


@mcp.tool()
def stats(library: str = "user") -> dict:
    """Show library statistics: total items, PDFs, notes, types, collections, top tags.

    Args:
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_stats(library=library)


@mcp.tool()
def update_status(
    key: str | None = None,
    collection: str | None = None,
    limit: int = 50,
    apply: bool = False,
    library: str = "user",
) -> dict:
    """Check if preprints (arXiv, bioRxiv, medRxiv) have been formally published.

    Uses the Semantic Scholar API to look up publication status.
    Set apply=True to update Zotero metadata for published items.

    Args:
        key: Optional single item key to check.
        collection: Optional collection name to filter items.
        limit: Maximum number of items to check (default 50).
        apply: If True, update Zotero metadata for published items (default False).
        library: Library — 'user' (default) or 'group:<id>'.
    """
    return _handle_update_status(key=key, collection=collection, limit=limit, apply=apply, library=library)
