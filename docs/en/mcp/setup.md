# MCP Server Setup

zotero-cli-ai supports [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) and can be used in MCP-compatible AI clients.

## Install MCP Support

```bash
pip install zotero-cli-ai[mcp]
```

## Start the Server

```bash
zot mcp serve
```

## Client Configuration

=== "Claude Desktop"

    Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

    ```json
    {
      "mcpServers": {
        "zotero": {
          "command": "zot",
          "args": ["mcp", "serve"]
        }
      }
    }
    ```

=== "Cursor"

    Edit `.cursor/mcp.json` in your project or global settings:

    ```json
    {
      "mcpServers": {
        "zotero": {
          "command": "zot",
          "args": ["mcp", "serve"]
        }
      }
    }
    ```

=== "LM Studio"

    In LM Studio settings, add MCP server:

    ```json
    {
      "mcpServers": {
        "zotero": {
          "command": "zot",
          "args": ["mcp", "serve"]
        }
      }
    }
    ```

## Verify Connection

After configuring, the AI client should show 45 available Zotero tools. Try asking:

> "Search my Zotero library for papers about attention mechanisms"
