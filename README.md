# zot — A Zotero CLI for Any AI Agent

<p align="center">
  <img src="asserts/banner_official.png" alt="zotero-cli banner" width="720">
</p>

<p align="center">
  <a href="https://pypi.org/project/zotero-cli-ai/"><img src="https://img.shields.io/pypi/v/zotero-cli-ai?color=blue" alt="PyPI version"></a>
  <a href="https://github.com/Agents365-ai/zotero-cli-ai/actions/workflows/ci.yml"><img src="https://github.com/Agents365-ai/zotero-cli-ai/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/zotero-cli-ai/"><img src="https://img.shields.io/pypi/pyversions/zotero-cli-ai" alt="Python versions"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/license-AGPL--3.0%20%2B%20Commercial-blue" alt="License"></a>
  <a href="https://agents365-ai.github.io/zotero-cli-ai/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-blue" alt="Docs"></a>
</p>

[中文](README_CN.md) | [Documentation](https://agents365-ai.github.io/zotero-cli-ai/)

`zotero-cli` is a Zotero CLI for any AI agent.

- **Reads** — direct local SQLite, zero-config, offline, millisecond response
- **Writes** — safe via Zotero Web API, Zotero stays in sync
- **PDF + ranked search** — extract full text with caching; index-free ranked retrieval over the whole library or scoped to a collection
- **Agent-native** — stable JSON envelope, typed exit codes, `zot schema`, `--dry-run`, `--idempotency-key`, NDJSON streaming
- **MCP server** — exposes 39 tools to Claude Desktop / LM Studio / Cursor via `zot mcp serve`

## Architecture

<p align="center">
  <img src="asserts/architecture.png" alt="Architecture diagram" width="720">
</p>

## Install

```bash
uv tool install zotero-cli-ai      # recommended
pipx install zotero-cli-ai         # or
pip install zotero-cli-ai          # or
```

> **Note:** the PyPI package is `zotero-cli-ai` (`zotero-cli` is an unrelated older project); the installed command is `zot`.

## 60-second quickstart

```bash
# Reads work out of the box — no API key, Zotero data dir auto-detected
zot search "transformer attention"
zot read ABC123
zot export ABC123                  # BibTeX

# Writes need a Web API key (https://www.zotero.org/settings/keys)
zot config init
zot add --doi "10.1038/s41586-023-06139-9"
```

In Claude Code, just ask in natural language — the bundled skill maps requests to `zot` commands automatically:

```bash
cp -r skill/zotero-cli ~/.claude/skills/
```

When stdout is not a TTY, `zot` automatically emits a stable JSON envelope so agents never need `--json`:

```json
{ "ok": true, "data": { ... }, "meta": { "request_id": "...", "cli_version": "0.4.3" } }
```

## Documentation

Full docs live at **<https://agents365-ai.github.io/zotero-cli-ai/>**.

| Topic | Link |
| --- | --- |
| Installation & setup | [Getting started](https://agents365-ai.github.io/zotero-cli-ai/getting-started/installation/) |
| Search, list, read | [Search guide](https://agents365-ai.github.io/zotero-cli-ai/guide/search/) |
| Notes, tags, citations | [Notes & tags](https://agents365-ai.github.io/zotero-cli-ai/guide/notes-tags/), [Citations](https://agents365-ai.github.io/zotero-cli-ai/guide/citations/) |
| Add / update / delete items | [Item management](https://agents365-ai.github.io/zotero-cli-ai/guide/item-management/) |
| Collections | [Collections](https://agents365-ai.github.io/zotero-cli-ai/guide/collections/) |
| Ranked search & ask (collections) | [Search guide](https://agents365-ai.github.io/zotero-cli-ai/guide/search/) |
| PDF extraction | [PDF](https://agents365-ai.github.io/zotero-cli-ai/guide/pdf/) |
| Preprint → published | [update-status](https://agents365-ai.github.io/zotero-cli-ai/guide/update-status/) |
| MCP setup & tools | [MCP](https://agents365-ai.github.io/zotero-cli-ai/mcp/setup/) |
| Full CLI reference | [CLI reference](https://agents365-ai.github.io/zotero-cli-ai/reference/cli/) |
| Agent contract (envelope, exit codes, schema) | [`docs/agent-interface.md`](docs/agent-interface.md) |
| Comparison with similar tools | [Comparison](https://agents365-ai.github.io/zotero-cli-ai/comparison/) |
| Roadmap | [`ROADMAP.md`](ROADMAP.md) |

**Why zotero-cli?** The only actively maintained Python CLI that reads Zotero's local SQLite database directly, with a clean read/write split: SQLite for fast offline reads, Web API for safe writes that Zotero stays aware of. See the [comparison page](https://agents365-ai.github.io/zotero-cli-ai/comparison/) for a feature-by-feature breakdown against similar tools.

## Support

If `zot` helps you, consider supporting the author:

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/wechat-pay.png" width="180" alt="WeChat Pay">
      <br>
      <b>WeChat Pay</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/alipay.png" width="180" alt="Alipay">
      <br>
      <b>Alipay</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/buymeacoffee.png" width="180" alt="Buy Me a Coffee">
      <br>
      <b>Buy Me a Coffee</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/awarding/award.gif" width="180" alt="Give a Reward">
      <br>
      <b>Give a Reward</b>
    </td>
  </tr>
</table>

## Author

**Agents365-ai**

- Bilibili: <https://space.bilibili.com/441831884>
- GitHub: <https://github.com/Agents365-ai>

## License

zotero-cli is **dual-licensed**:

- **Open source:** [GNU AGPL-3.0-or-later](https://www.gnu.org/licenses/agpl-3.0) (see [LICENSE](LICENSE)).
- **Commercial:** a separate commercial license is available for use in
  closed-source or commercial products without the AGPL's copyleft obligations
  (see [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL)).

Contributions are accepted under the project's [Developer Certificate of Origin](CONTRIBUTING.md).
