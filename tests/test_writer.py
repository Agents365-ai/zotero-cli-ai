from unittest.mock import MagicMock, patch

import httpx
import pytest

from zotero_cli_cc.core import writer
from zotero_cli_cc.core.writer import ZoteroWriteError, ZoteroWriter


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_writer_init(mock_zotero_cls):
    ZoteroWriter(library_id="123", api_key="abc")
    mock_zotero_cls.assert_called_once_with("123", "user", "abc")


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_note(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item_template.return_value = {"itemType": "note", "note": "", "parentItem": ""}
    mock_zot.create_items.return_value = {"successful": {"0": {"key": "N1"}}}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    result = writer.add_note("PARENT1", "My note content")
    assert result == "N1"
    mock_zot.create_items.assert_called_once()


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_standalone_note(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item_template.return_value = {"itemType": "note", "note": "", "parentItem": ""}
    mock_zot.create_items.return_value = {"successful": {"0": {"key": "N2"}}}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    result = writer.add_standalone_note("My note content")
    assert result == "N2"
    template = mock_zot.create_items.call_args[0][0][0]
    # A top-level note must not carry a parentItem key
    assert "parentItem" not in template


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_standalone_note_network_error(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item_template.return_value = {"itemType": "note", "note": "", "parentItem": ""}
    from httpx import ConnectError

    mock_zot.create_items.side_effect = ConnectError("Network unreachable")

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="Network"):
        writer.add_standalone_note("content")


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_tags(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item.return_value = {"key": "K1", "data": {"tags": [{"tag": "old"}]}}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    writer.add_tags("K1", ["new1", "new2"])
    mock_zot.update_item.assert_called_once()


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_delete_item(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item.return_value = {"key": "K1", "data": {"deleted": 0}}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    writer.delete_item("K1")
    mock_zot.delete_item.assert_called_once()


# --- Error-path tests ---


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_note_network_error(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item_template.return_value = {"itemType": "note", "note": "", "parentItem": ""}
    from httpx import ConnectError

    mock_zot.create_items.side_effect = ConnectError("Network unreachable")

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="Network"):
        writer.add_note("P1", "content")


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_note_api_failure(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item_template.return_value = {"itemType": "note", "note": "", "parentItem": ""}
    mock_zot.create_items.return_value = {"successful": {}, "failed": {"0": {"message": "Bad request"}}}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="Bad request"):
        writer.add_note("P1", "content")


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_delete_item_not_found(mock_zotero_cls):
    from pyzotero.zotero_errors import ResourceNotFoundError

    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item.side_effect = ResourceNotFoundError("Not found")

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="not found"):
        writer.delete_item("NONEXIST")


# --- Collection management tests ---


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_delete_collection(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.collection.return_value = {"key": "COL1", "version": 1}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    writer.delete_collection("COL1")
    mock_zot.collection.assert_called_once_with("COL1")
    mock_zot.delete_collection.assert_called_once()


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_delete_collection_not_found(mock_zotero_cls):
    from pyzotero.zotero_errors import ResourceNotFoundError

    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.collection.side_effect = ResourceNotFoundError("Not found")

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="not found"):
        writer.delete_collection("NONEXIST")


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_rename_collection(mock_zotero_cls):
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.collection.return_value = {"key": "COL1", "data": {"name": "Old Name"}, "version": 1}

    writer = ZoteroWriter(library_id="123", api_key="abc")
    writer.rename_collection("COL1", "New Name")
    mock_zot.collection.assert_called_once_with("COL1")
    mock_zot.update_collection.assert_called_once()
    # Verify the name was updated in the payload
    call_args = mock_zot.update_collection.call_args[0][0]
    assert call_args["data"]["name"] == "New Name"


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_rename_collection_not_found(mock_zotero_cls):
    from pyzotero.zotero_errors import ResourceNotFoundError

    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.collection.side_effect = ResourceNotFoundError("Not found")

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="not found"):
        writer.rename_collection("NONEXIST", "New Name")


# --- httpx / httpx2 dual-stack compatibility (issue #109) ---


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_timeout_lands_as_scalar_slots(mock_zotero_cls):
    # A Timeout object fed into pyzotero's client crashes socket.settimeout()
    # on the first request; the assigned value must be a plain float.
    client = httpx.Client()
    mock_zot = MagicMock()
    mock_zot.client = client
    mock_zotero_cls.return_value = mock_zot

    ZoteroWriter(library_id="123", api_key="abc", timeout=30.0)
    timeout = client.timeout
    assert all(isinstance(getattr(timeout, slot), (int, float)) for slot in ("connect", "read", "write", "pool"))


def test_network_errors_cover_httpx2_stack():
    httpx2 = pytest.importorskip("httpx2")
    assert httpx2.ConnectError in writer._network_errors
    assert httpx2.TimeoutException in writer._network_errors
    assert httpx.ConnectError in writer._network_errors
    assert httpx.TimeoutException in writer._network_errors


@patch("zotero_cli_cc.core.writer.zotero.Zotero")
def test_add_standalone_note_httpx2_network_error(mock_zotero_cls):
    # pyzotero >= 1.15 raises its vendored httpx2 exceptions; they must still
    # map to a retryable ZoteroWriteError.
    httpx2 = pytest.importorskip("httpx2")
    mock_zot = MagicMock()
    mock_zotero_cls.return_value = mock_zot
    mock_zot.item_template.return_value = {"itemType": "note", "note": "", "parentItem": ""}
    mock_zot.create_items.side_effect = httpx2.ConnectError("Network unreachable")

    writer = ZoteroWriter(library_id="123", api_key="abc")
    with pytest.raises(ZoteroWriteError, match="Network") as excinfo:
        writer.add_standalone_note("content")
    assert excinfo.value.code == "network_error"
    assert excinfo.value.retryable is True
