from __future__ import annotations

import click

from zotero_cli_cc.commands._helpers import open_reader
from zotero_cli_cc.config import load_config
from zotero_cli_cc.core.rank import make_snippet, rank, resolve_collection_key
from zotero_cli_cc.exit_codes import emit_error
from zotero_cli_cc.formatter import format_items, format_ranked_results, stream_items


@click.command("search")
@click.argument("query")
@click.option(
    "--collection",
    default=None,
    help="Filter by Zotero collection (folder) name. Use 'zot collection list' to see available names.",
)
@click.option("--type", "item_type", default=None, help="Filter by item type (e.g. journalArticle, book, preprint)")
@click.option(
    "--ranked",
    is_flag=True,
    help="Relevance-ranked mode: idf-weighted full-text + metadata fusion with scores and "
    "snippets (ignores --sort/--type/--stream).",
)
@click.option(
    "--sort",
    default=None,
    type=click.Choice(["dateAdded", "dateModified", "title", "creator"]),
    help="Sort results by field",
)
@click.option(
    "--direction",
    default="desc",
    type=click.Choice(["asc", "desc"]),
    help="Sort direction (default: desc)",
)
@click.option("--limit", default=None, type=int, help="Limit results (overrides global --limit)")
@click.option("--stream", is_flag=True, help="Emit NDJSON (one item per line) for incremental processing")
@click.pass_context
def search_cmd(
    ctx: click.Context,
    query: str,
    collection: str | None,
    item_type: str | None,
    ranked: bool,
    sort: str | None,
    direction: str,
    limit: int | None,
    stream: bool,
) -> None:
    """Search the Zotero library by title, author, tag, or full text.

    \b
    Examples:
      zot search "transformer attention"
      zot search "GAN" --limit 5
      zot --json search "single cell"

    \b
    Filter by Zotero collection (folder):
      zot collection list                        # show available collections
      zot search "BERT" --collection "NLP"       # search within "NLP" collection

    \b
    Relevance-ranked deep search (scores + snippets, always fresh):
      zot search "RLHF reward hacking" --ranked
      zot --json search "tumour immunity" --ranked --collection "CR | HCC"
    """
    cfg = load_config(profile=ctx.obj.get("profile"))
    with open_reader(ctx, cfg) as reader:
        limit = limit if limit is not None else ctx.obj.get("limit", cfg.default_limit)
        json_out = ctx.obj.get("json", False)
        if ranked:
            collection_key = None
            if collection:
                collection_key = resolve_collection_key(reader, collection)
                if collection_key is None:
                    emit_error(
                        "not_found",
                        f"Collection '{collection}' not found",
                        output_json=json_out,
                        hint="Use 'zot collection list' to see available collections",
                        context="search",
                    )
            results = rank(reader, query, collection_key=collection_key, top_k=limit)
            if not results:
                if json_out:
                    click.echo(format_ranked_results([], question=query, collection=collection, output_json=True))
                else:
                    click.echo("No results found.", err=True)
                return
            for r in results:
                r["snippet"] = make_snippet(r["item"], r["terms"])
            click.echo(format_ranked_results(results, question=query, collection=collection, output_json=json_out))
            return
        try:
            result = reader.search(
                query, collection=collection, item_type=item_type, sort=sort, direction=direction, limit=limit
            )
        except ValueError as e:
            emit_error("validation_error", str(e), output_json=json_out)
        detail = ctx.obj.get("detail", "standard")
        if stream:
            click.echo(stream_items(result.items, detail=detail))
            return
        if not result.items:
            if json_out:
                click.echo(format_items([], output_json=True))
            else:
                click.echo("No results found.", err=True)
            return
        click.echo(format_items(result.items, output_json=json_out, detail=detail))
