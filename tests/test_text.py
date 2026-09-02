from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from zotero_cli_cc.cli import main
from zotero_cli_cc.core.pdf_cache import PdfCache


def _run(args: list[str], data_dir: Path) -> Result:
    runner = CliRunner()
    return runner.invoke(
        main,
        args,
        env={"ZOT_DATA_DIR": str(data_dir), "ZOT_FORMAT": "table"},
    )


def test_text_extracts_and_writes_per_item_files(test_data_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "text"
    result = _run(["text", "--dir", str(out)], test_data_dir)
    assert result.exit_code == 0
    f = out / "ATTN001.txt"
    assert f.exists()
    content = f.read_text()
    assert content.startswith("Title: ")
    assert len(content) > len("Title: \nAuthors: \n\n")


def test_text_only_cached_uses_seeded_entries(test_data_dir: Path, tmp_path: Path) -> None:
    from zotero_cli_cc.core.reader import ZoteroReader

    out = tmp_path / "text"
    reader = ZoteroReader(test_data_dir / "zotero.sqlite")
    att = reader.get_pdf_attachment("ATTN001")
    assert att is not None and att.path is not None
    cache = PdfCache()
    cache.put(att.path, "pdfium", "seed body mark")
    try:
        result = _run(["text", "--dir", str(out), "--only-cached"], test_data_dir)
        assert result.exit_code == 0
        assert (out / "ATTN001.txt").read_text().endswith("seed body mark")
    finally:
        cache.close()


def test_text_writes_metadata_only_for_items_without_pdf(test_data_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "text"
    result = _run(["text", "--dir", str(out), "--only-cached"], test_data_dir)
    assert result.exit_code == 0
    f = out / "DEEP003.txt"
    assert f.exists()
    content = f.read_text()
    assert content.startswith("Title: ")
    assert "Abstract:" in content
