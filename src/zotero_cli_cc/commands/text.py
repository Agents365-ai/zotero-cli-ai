"""Materialize every item's text into per-item .txt files for grep.

One file per item, named by the item key, so `grep -r "term" <dir>` returns
hits whose filename is the key for `zot read <key>` / `zot open <key>`. The
body is the item's first PDF attachment's text (via the on-disk PdfCache,
extracting missing PDFs in parallel worker processes unless --only-cached);
items without a usable PDF get their metadata block only
(title/authors/abstract/tags).
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click

from zotero_cli_cc.commands._helpers import open_reader
from zotero_cli_cc.config import load_pdf_config
from zotero_cli_cc.core.pdf_cache import PdfCache
from zotero_cli_cc.formatter import emit_progress, envelope_ok
from zotero_cli_cc.models import Item

DEFAULT_TEXT_DIR = Path.home() / ".config" / "zot" / "text"


def _extract_subprocess(pdf_path: str, extractor_name: str) -> str:
    """Extract one PDF in a worker subprocess; raise on crash/timeout.

    pdfium's C library is not thread-safe (pypdfium2 docs: concurrent use
    needs custom locking and can segfault), so each PDF is extracted by its
    own short-lived process; a poison PDF dies alone and just counts as
    skipped. Cache writes happen inside the worker.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "zotero_cli_cc.core.pdf_extract_worker", pdf_path, extractor_name],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip()[-200:]
        raise RuntimeError(f"extractor exited {proc.returncode}: {tail}")
    try:
        text = json.loads(proc.stdout)
    except ValueError as e:
        raise RuntimeError(f"invalid worker output: {e}") from e
    if not isinstance(text, str) or not text:
        raise RuntimeError("worker returned non-string or empty text")
    return text


def _metadata_header(item: Item) -> str:
    """Title/authors/abstract/tags header, also the whole body for PDF-less items."""
    lines = [f"Title: {item.title or ''}", f"Authors: {', '.join(c.full_name for c in item.creators)}"]
    if item.abstract:
        lines.append(f"Abstract: {item.abstract}")
    if item.tags:
        lines.append(f"Tags: {', '.join(item.tags)}")
    return "\n".join(lines) + "\n"


@click.command("text")
@click.option(
    "--dir",
    "out_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_TEXT_DIR,
    show_default=True,
    help="Directory to write <itemkey>.txt files",
)
@click.option(
    "--only-cached",
    is_flag=True,
    help="Use only text already in the cache; never extract PDFs (instant, offline)",
)
@click.option(
    "--workers",
    default=4,
    show_default=True,
    help="Parallel PDF extraction processes",
)
@click.pass_context
def text_cmd(ctx: click.Context, out_dir: Path, only_cached: bool, workers: int) -> None:
    """Write each item's PDF full text to <dir>/<itemkey>.txt for grep.

    \b
    Examples:
      zot text                             Dump the whole corpus (default dir)
      zot text --dir ~/zot-text            Custom directory
      zot text --only-cached               Only already-extracted text, offline
      grep -r "reward hacking" ~/zot-text  # hit filename = item key
    """
    json_out = ctx.obj.get("json", False)
    out_dir.mkdir(parents=True, exist_ok=True)
    extractor = load_pdf_config().extractor
    written = extracted = skipped = no_pdf = 0
    emit_progress("start", phase="text", dir=str(out_dir))
    with open_reader(ctx) as reader:
        result = reader.search("", limit=10_000_000)
        items = list(result.items)
        total = len(items)
        pending: list[tuple[Item, Path]] = []  # extraction fan-out for the pool
        cache = PdfCache()
        for item in items:
            attachment = reader.get_pdf_attachment(item.key)
            header = _metadata_header(item)
            if attachment is None or attachment.path is None or not attachment.path.exists():
                # No usable PDF: write the metadata block alone so every item
                # stays grep-able (title/abstract hits still map to the key).
                (out_dir / f"{item.key}.txt").write_text(header)
                written += 1
                no_pdf += 1
                continue
            text = cache.get(attachment.path, extractor)
            if text is not None:
                (out_dir / f"{item.key}.txt").write_text(header + text)
                written += 1
            elif not only_cached:
                # Header written first so partial runs still yield a usable file.
                (out_dir / f"{item.key}.txt").write_text(header)
                pending.append((item, attachment.path))

        done = total - len(pending)
        emit_progress("progress", phase="text", done=done, total=total)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_extract_subprocess, str(path), extractor): item for item, path in pending}
            for fut in as_completed(futures):
                item = futures[fut]
                try:
                    text = fut.result()
                except Exception:
                    skipped += 1
                    continue
                extracted += 1
                (out_dir / f"{item.key}.txt").write_text(_metadata_header(item) + text)
                written += 1
                done += 1
                if total >= 100 and done % max(1, total // 20) == 0:
                    emit_progress("progress", phase="text", done=done, total=total)
    cache.close()
    emit_progress("complete", phase="text", done=total, total=total)
    stats = {
        "dir": str(out_dir),
        "written": written,
        "extracted": extracted,
        "metadata_only": no_pdf,
        "skipped": skipped,
    }
    if json_out:
        click.echo(json.dumps(envelope_ok(stats), indent=2, ensure_ascii=False))
    else:
        click.echo(
            f"Wrote {written} text files to {out_dir} ({extracted} extracted, {no_pdf} metadata-only, {skipped} skipped)"
        )
