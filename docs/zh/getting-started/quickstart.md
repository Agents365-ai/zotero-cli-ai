# 快速开始

[安装](installation.md) zot 后，即可搜索和阅读论文。

## 1. 搜索文献库

```bash
zot search "transformer attention"
```

在标题、作者、标签和 PDF 全文索引中搜索关键词。

## 2. 阅读论文

从搜索结果中选择一个条目键（如 `ABC123`）：

```bash
zot read ABC123
```

显示完整的元数据、摘要和笔记。

## 3. 提取 PDF 文本

```bash
zot pdf ABC123
```

从论文的 PDF 附件中提取全文。使用 `--pages 1-5` 指定页码范围。

## AI 友好的 JSON 输出

在任何命令前添加 `--json` 获取机器可读输出：

```bash
zot --json search "single cell RNA"
```

这是 Claude Code 在后台与论文交互时使用的格式。

## 搭配 Claude Code 使用

安装 zotero-cli skill，让 Claude Code 自动识别文献相关请求：

```bash
cp -r skill/zotero-cli ~/.claude/skills/
```

然后在任何 Claude Code 会话中使用自然语言：

```
搜索我的 Zotero 中关于单细胞的论文
→ Claude 运行: zot --json search "single cell"

查看这篇论文的详情
→ Claude 运行: zot --json read ABC123
```

## 下一步

- [使用指南](../guide/search.md) — 完整命令参考
- [MCP 服务器](../mcp/setup.md) — 搭配 Claude Desktop、Cursor、LM Studio 使用
- [工作区](../guide/workspace.md) — 按主题组织论文，支持 RAG 检索
