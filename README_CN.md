# zot — 适配任意 AI Agent 的 Zotero 命令行工具

<p align="center">
  <img src="asserts/banner_official.png" alt="zotero-cli banner" width="720">
</p>

<p align="center">
  <a href="https://pypi.org/project/zotero-cli-ai/"><img src="https://img.shields.io/pypi/v/zotero-cli-ai?color=blue" alt="PyPI version"></a>
  <a href="https://github.com/Agents365-ai/zotero-cli-ai/actions/workflows/ci.yml"><img src="https://github.com/Agents365-ai/zotero-cli-ai/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/zotero-cli-ai/"><img src="https://img.shields.io/pypi/pyversions/zotero-cli-ai" alt="Python versions"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/license-AGPL--3.0%20%2B%20Commercial-blue" alt="License"></a>
  <a href="https://agents365-ai.github.io/zotero-cli-ai/zh/"><img src="https://img.shields.io/badge/文档-GitHub%20Pages-blue" alt="文档"></a>
</p>

[English](README.md) | [文档](https://agents365-ai.github.io/zotero-cli-ai/zh/)

`zotero-cli` 是一个适配任意 AI Agent 的 Zotero 命令行工具。

- **读操作** — 直接读取本地 SQLite，零配置、离线可用、毫秒级响应
- **写操作** — 通过 Zotero Web API 安全写入，Zotero 完全感知变更
- **PDF + 排序检索** — 提取 PDF 全文并自动缓存；免索引两阶段排序检索，覆盖全库或指定分类（Collection）
- **Agent-native** — 稳定 JSON envelope、类型化退出码、`zot schema`、`--dry-run`、`--idempotency-key`、NDJSON 流
- **MCP 服务器** — 通过 `zot mcp serve` 向 Claude Desktop / LM Studio / Cursor 暴露 39 个工具

## 架构

<p align="center">
  <img src="asserts/architecture.png" alt="Architecture diagram" width="720">
</p>

## 安装

```bash
uv tool install zotero-cli-ai      # 推荐
pipx install zotero-cli-ai         # 或者
pip install zotero-cli-ai          # 或者
```

> **注意：** PyPI 包名为 `zotero-cli-ai`（`zotero-cli` 是无关的早期项目），安装后的命令为 `zot`。

## 60 秒上手

```bash
# 读操作开箱即用 —— 无需 API Key，自动检测 Zotero 数据目录
zot search "transformer attention"
zot read ABC123
zot export ABC123                  # BibTeX

# 写操作需要 Web API Key（https://www.zotero.org/settings/keys）
zot config init
zot add --doi "10.1038/s41586-023-06139-9"
```

在 Claude Code 中直接用自然语言提问——配套 skill 会自动把请求映射到 `zot` 命令：

```bash
cp -r skill/zotero-cli ~/.claude/skills/
```

当 stdout 不是终端时，`zot` 自动输出稳定的 JSON envelope，Agent 调用无需加 `--json`：

```json
{ "ok": true, "data": { ... }, "meta": { "request_id": "...", "cli_version": "0.4.3" } }
```

## 文档

完整文档：**<https://agents365-ai.github.io/zotero-cli-ai/zh/>**

| 主题 | 链接 |
| --- | --- |
| 安装与配置 | [快速开始](https://agents365-ai.github.io/zotero-cli-ai/zh/getting-started/installation/) |
| 搜索、列表、阅读 | [搜索指南](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/search/) |
| 笔记、标签、引用 | [笔记与标签](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/notes-tags/)、[引用导出](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/citations/) |
| 增 / 改 / 删条目 | [条目管理](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/item-management/) |
| 分类（Collection） | [Collections](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/collections/) |
| 工作空间（即 Collection） | [Workspace](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/workspace/) |
| PDF 提取 | [PDF](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/pdf/) |
| 预印本 → 已发表 | [update-status](https://agents365-ai.github.io/zotero-cli-ai/zh/guide/update-status/) |
| MCP 配置与工具 | [MCP](https://agents365-ai.github.io/zotero-cli-ai/zh/mcp/setup/) |
| 完整 CLI 参考 | [CLI Reference](https://agents365-ai.github.io/zotero-cli-ai/zh/reference/cli/) |
| Agent 契约（envelope、退出码、schema） | [`docs/agent-interface.md`](docs/agent-interface.md) |
| 同类工具对比 | [Comparison](https://agents365-ai.github.io/zotero-cli-ai/zh/comparison/) |
| 开发路线图 | [`ROADMAP.md`](ROADMAP.md) |

**为什么选 zotero-cli？** 当前唯一仍在维护、直接读取 Zotero 本地 SQLite 的 Python CLI；读写分离架构 —— SQLite 提供快速离线读，Web API 提供让 Zotero 感知的安全写。完整功能对比见[对比页面](https://agents365-ai.github.io/zotero-cli-ai/zh/comparison/)。

## 社区

欢迎加入获取帮助、问答和更新：

- **Discord：** <https://discord.gg/79JF5Atuk>
- **微信：** 扫描下方二维码

<p align="center">
  <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/agents365ai_wechat_1.png" width="200" alt="微信交流群">
</p>

## 赞助

如果 `zot` 对你有帮助，欢迎赞助作者：

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/wechat-pay.png" width="180" alt="微信支付">
      <br>
      <b>微信支付</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/alipay.png" width="180" alt="支付宝">
      <br>
      <b>支付宝</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/buymeacoffee.png" width="180" alt="Buy Me a Coffee">
      <br>
      <b>Buy Me a Coffee</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/awarding/award.gif" width="180" alt="打赏">
      <br>
      <b>打赏</b>
    </td>
  </tr>
</table>

## 作者

**Agents365-ai**

- Bilibili：<https://space.bilibili.com/441831884>
- GitHub：<https://github.com/Agents365-ai>

## 许可证

zotero-cli 采用**双许可证**：

- **开源：** [GNU AGPL-3.0-or-later](https://www.gnu.org/licenses/agpl-3.0)（见 [LICENSE](LICENSE)）。
- **商业：** 如需在闭源或商业产品中使用而不受 AGPL 的 copyleft 义务约束，
  可获取单独的商业许可证（见 [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL)）。

贡献代码需遵循项目的 [Developer Certificate of Origin](CONTRIBUTING.md)。
