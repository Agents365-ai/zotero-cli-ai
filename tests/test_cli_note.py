import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from zotero_cli_cc.cli import main
from zotero_cli_cc.exit_codes import EXIT_VALIDATION
from zotero_cli_cc.models import Note


def test_note_read(test_db_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "ATTN001"],
        env={"ZOT_DATA_DIR": str(test_db_path.parent), "ZOT_FORMAT": "table"},
    )
    assert result.exit_code == 0
    assert "transformer architecture" in result.output


def test_note_read_json(test_db_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--json", "note", "ATTN001"],
        env={"ZOT_DATA_DIR": str(test_db_path.parent), "ZOT_FORMAT": "table"},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)["data"]
    assert len(data) >= 1


@patch("zotero_cli_cc.commands._helpers.ZoteroWriter")
def test_note_add_converts_markdown_to_html(mock_writer_cls, test_db_path):
    mock_writer = MagicMock()
    mock_writer_cls.return_value = mock_writer
    mock_writer.add_note.return_value = "NEWNOTE"

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "ATTN001", "--add", "**New note**"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == 0
    mock_writer.add_note.assert_called_once_with("ATTN001", "<p><strong>New note</strong></p>")


@patch("zotero_cli_cc.commands._helpers.ZoteroWriter")
def test_note_add_raw_stores_verbatim(mock_writer_cls, test_db_path):
    mock_writer = MagicMock()
    mock_writer_cls.return_value = mock_writer
    mock_writer.add_note.return_value = "NEWNOTE"

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "ATTN001", "--add", "<p>New note</p>", "--raw"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == 0
    mock_writer.add_note.assert_called_once_with("ATTN001", "<p>New note</p>")


def test_note_add_dry_run_previews_converted_html(test_db_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "ATTN001", "--add", "# Heading\n**bold**", "--dry-run"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == 0
    assert "Would add note" in result.output
    assert "<h1>Heading</h1>" in result.output
    assert "<strong>bold</strong>" in result.output


@patch("zotero_cli_cc.commands.note.open_reader")
def test_note_standalone_list(mock_open_reader, test_db_path):
    reader = MagicMock()
    mock_open_reader.return_value.__enter__.return_value = reader
    reader.get_standalone_notes.return_value = [Note(key="STAN001", parent_key="", content="standalone note")]

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "--standalone"],
        env={"ZOT_DATA_DIR": str(test_db_path.parent), "ZOT_FORMAT": "table"},
    )
    assert result.exit_code == 0
    assert "STAN001" in result.output


@patch("zotero_cli_cc.commands._helpers.ZoteroWriter")
def test_note_add_standalone_converts_markdown(mock_writer_cls, test_db_path):
    mock_writer = MagicMock()
    mock_writer_cls.return_value = mock_writer
    mock_writer.add_standalone_note.return_value = "STAN001"

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "--standalone", "--add", "**New note**"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == 0
    mock_writer.add_standalone_note.assert_called_once_with("<p><strong>New note</strong></p>")


def test_note_add_requires_key_or_standalone(test_db_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "--add", "x"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == EXIT_VALIDATION


def test_note_standalone_rejects_key(test_db_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "ATTN001", "--standalone", "--add", "x"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == EXIT_VALIDATION


def test_note_add_standalone_dry_run(test_db_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["note", "--standalone", "--add", "# Heading\n**bold**", "--dry-run"],
        env={
            "ZOT_DATA_DIR": str(test_db_path.parent),
            "ZOT_LIBRARY_ID": "123",
            "ZOT_API_KEY": "abc",
            "ZOT_FORMAT": "table",
        },
    )
    assert result.exit_code == 0
    assert "Would add standalone note" in result.output
    assert "<h1>Heading</h1>" in result.output
