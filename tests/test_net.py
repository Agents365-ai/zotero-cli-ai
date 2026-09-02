from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from zotero_cli_cc.cli import main


def _run(args: list[str], data_dir: Path) -> Result:
    runner = CliRunner()
    return runner.invoke(
        main,
        args,
        env={"ZOT_DATA_DIR": str(data_dir), "ZOT_FORMAT": "table"},
    )


def test_net_writes_interactive_html(test_data_dir: Path, tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    pytest.importorskip("pyvis")
    out = tmp_path / "g.html"
    result = _run(["net", "--out", str(out)], test_data_dir)
    assert result.exit_code == 0
    html = out.read_text()
    assert "vis" in html.lower() or "graph" in html.lower()
    assert "visjs" in html.lower() or "graph2d" in html.lower() or "DataSet" in html


def test_net_seed_mode_expands_neighbours(test_data_dir: Path, tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    pytest.importorskip("pyvis")
    out = tmp_path / "seed.html"
    result = _run(["net", "--seed", "ATTN001", "--out", str(out)], test_data_dir)
    assert result.exit_code == 0
    html = out.read_text()
    assert "attention" in html.lower()


def test_net_unknown_seed_error(test_data_dir: Path, tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    pytest.importorskip("pyvis")
    result = _run(["net", "--seed", "NOPE", "--out", str(tmp_path / "x.html")], test_data_dir)
    assert result.exit_code != 0
