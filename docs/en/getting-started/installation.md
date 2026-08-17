# Installation

## Requirements

- Python 3.10 or later
- A local Zotero installation (for the SQLite database)

## Install

=== "uv (recommended)"

    ```bash
    uv tool install zotero-cli-ai
    ```

=== "pipx"

    ```bash
    pipx install zotero-cli-ai
    ```

=== "pip"

    ```bash
    pip install zotero-cli-ai
    ```

## Upgrade

=== "uv"

    ```bash
    uv tool upgrade zotero-cli-ai
    ```

=== "pipx"

    ```bash
    pipx upgrade zotero-cli-ai
    ```

=== "pip"

    ```bash
    pip install -U zotero-cli-ai
    ```

## MCP Support

To use zotero-cli-ai as an MCP server (for Claude Desktop, Cursor, LM Studio):

```bash
pip install zotero-cli-ai[mcp]
```

## Verify Installation

```bash
zot --version
```
