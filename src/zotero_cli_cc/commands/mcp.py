"""MCP server CLI commands."""

from __future__ import annotations

import click


@click.group("mcp")
def mcp_group() -> None:
    """MCP server commands."""
    pass


@mcp_group.command("serve")
def serve_cmd() -> None:
    """Start MCP server on stdio for use with LM Studio, Claude Desktop, etc."""
    try:
        from zotero_cli_cc.mcp_server import mcp as mcp_server
    except ImportError:
        click.echo(
            "Error: MCP support not installed.\nInstall with: pip install zotero-cli-ai[mcp]",
            err=True,
        )
        raise SystemExit(1)
    mcp_server.run(transport="stdio")
