# 笔记与标签

## 查看笔记

```bash
zot note ABC123
```

显示附加到条目的所有笔记，从 HTML 转换为 Markdown。

## 添加笔记

```bash
zot note ABC123 --add "这篇论文提出了一种新的注意力机制"
```

!!! note "写入操作需要 API 凭据"
    请参阅 [配置](../getting-started/setup.md#api) 来设置 API 密钥。

### Markdown 处理

Zotero 以 HTML 存储笔记，因此 `--add` 会在提交前把 Markdown 转换为 HTML：

- 笔记开头的 YAML frontmatter（`--- ... ---`）会被剥离。
- Obsidian callout（`> [!type] text`）会转换为加粗文本的 blockquote。
- 标题、强调、列表、链接、代码和表格会渲染为 Zotero 格式。

传入 `--raw` 可以原样存储内容（例如当你已经有 HTML 时）：

```bash
zot note ABC123 --add "<p>Already <strong>HTML</strong>.</p>" --raw
```

!!! warning "不要直接提交 `**` Markdown"
    Zotero API 会把它无法解释的 Markdown 强调字符转义：提交 `**bold**` 会存储为 `\*\*bold\*\*`，在 Zotero 中渲染为字面文本。请始终让 `--add` 完成转换，或配合 `--raw` 传入 HTML。

## 更新笔记

可以通过 MCP 工具（`note_update`）更新笔记。参见 [MCP 工具参考](../mcp/tools.md)。

## 查看标签

```bash
zot tag ABC123
```

## 添加标签

```bash
zot tag ABC123 --add "important"
zot tag ABC123 --add "to-read" --add "attention"
```

## 删除标签

```bash
zot tag ABC123 --remove "to-read"
```

## 批量标签操作

可以通过 MCP 工具（`tag_add`、`tag_remove`）批量操作多个条目的标签。参见 [MCP 工具参考](../mcp/tools.md)。
