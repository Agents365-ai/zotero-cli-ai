"""Tests for `zot ask` — index-free, collection-backed evidence-pack command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from zotero_cli_cc.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _invoke(args: list[str], json_output: bool = False):
    runner = CliRunner()
    base = ["--json"] if json_output else []
    env = {"ZOT_DATA_DIR": str(FIXTURES_DIR), "ZOT_FORMAT": "table"}
    return runner.invoke(main, base + args, env=env)


def _envelope(output: str) -> dict:
    """`ask` emits NDJSON progress events before the final pretty-printed
    envelope; parse the trailing JSON document."""
    start = output.rfind("\n{\n")
    text = output[start + 1 :] if start >= 0 else output
    return json.loads(text)


class TestAskCLI:
    @patch("zotero_cli_cc.core.rank.convert_pdf_to_text", return_value="attention mechanism from the pdf")
    def test_ask_table(self, _mock_convert):
        result = _invoke(["ask", "attention"])
        assert result.exit_code == 0
        assert "ATTN001" in result.output

    @patch("zotero_cli_cc.core.rank.convert_pdf_to_text", return_value="attention mechanism from the pdf")
    def test_ask_json_envelope(self, _mock_convert):
        result = _invoke(["ask", "attention"], json_output=True)
        env = _envelope(result.output)
        assert env["ok"] is True
        data = env["data"]
        assert data["question"] == "attention"
        assert data["mode"] == "index-free"
        assert "answer_instructions" in data
        assert isinstance(data["evidence"], list) and len(data["evidence"]) > 0
        assert data["evidence"][0]["cite_key"] == "ATTN001"
        assert env["meta"]["retrieved"] == len(data["evidence"])

    @patch("zotero_cli_cc.core.rank.convert_pdf_to_text", return_value="attention mechanism from the pdf")
    def test_ask_pdf_passages_included(self, _mock_convert):
        result = _invoke(["ask", "attention"], json_output=True)
        data = _envelope(result.output)["data"]
        sources = {e["source"] for e in data["evidence"]}
        assert "pdf" in sources

    @patch("zotero_cli_cc.core.rank.convert_pdf_to_text", return_value="attention mechanism")
    def test_ask_collection_scope(self, _mock_convert):
        result = _invoke(["ask", "attention", "--collection", "Transformers"], json_output=True)
        data = _envelope(result.output)["data"]
        assert data["collection"] == "Transformers"
        cite_keys = {e["cite_key"] for e in data["evidence"]}
        assert cite_keys == {"ATTN001"}

    @patch("zotero_cli_cc.core.rank.convert_pdf_to_text", return_value="attention mechanism")
    def test_ask_evidence_k_caps(self, _mock_convert):
        result = _invoke(["ask", "attention", "--evidence-k", "1"], json_output=True)
        data = _envelope(result.output)["data"]
        assert len(data["evidence"]) <= 1

    def test_ask_unknown_collection(self):
        result = _invoke(["ask", "x", "--collection", "nope"])
        assert result.exit_code == 4
        assert "not found" in result.output.lower()

    def test_ask_no_evidence(self):
        result = _invoke(["ask", "zzzznotfound"], json_output=True)
        data = _envelope(result.output)["data"]
        assert data["evidence"] == []
