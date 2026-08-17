from __future__ import annotations

import click

from zotero_cli_cc.commands._helpers import open_reader
from zotero_cli_cc.core.rank import make_snippet, rank, resolve_collection_key
from zotero_cli_cc.exit_codes import emit_error
from zotero_cli_cc.formatter import format_workspace_query


@click.group("workspace")
def workspace_group() -> None:
    """Query a workspace — a workspace is simply a Zotero collection.

    Manage membership in the Zotero app (or via 'zot collection *'); zot
    stores nothing locally. There is no index to build: queries run live
    against Zotero's own full-text index, so results are always fresh.
    """
    pass


@workspace_group.command("query")
@click.argument("question")
@click.option(
    "--workspace",
    "ws_name",
    default=None,
    help="Scope to a collection (name or key). Default: whole library.",
)
@click.option("--top-k", default=5, help="Number of results (default: 5)")
@click.pass_context
def workspace_query(ctx: click.Context, question: str, ws_name: str | None, top_k: int) -> None:
    """Rank papers by relevance to a natural-language question.

    \b
    Examples:
      zot workspace query "RLHF reward hacking"
      zot --json workspace query "tumour immunity" --workspace "CR | HCC" --top-k 10
    """
    json_out = ctx.obj.get("json", False)
    with open_reader(ctx) as reader:
        collection_key = None
        if ws_name:
            collection_key = resolve_collection_key(reader, ws_name)
            if collection_key is None:
                emit_error(
                    "not_found",
                    f"Collection '{ws_name}' not found",
                    output_json=json_out,
                    hint="Use 'zot collection list' to see available collections",
                    context="workspace query",
                )
        results = rank(reader, question, collection_key=collection_key, top_k=top_k)
        if not results:
            if json_out:
                click.echo(format_workspace_query([], question=question, workspace=ws_name, output_json=True))
            else:
                click.echo("No results found.", err=True)
            return
        for r in results:
            r["snippet"] = make_snippet(r["item"], r["terms"])
        click.echo(format_workspace_query(results, question=question, workspace=ws_name, output_json=json_out))
