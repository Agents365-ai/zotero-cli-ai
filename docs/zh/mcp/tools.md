# MCP 工具参考

共 39 个工具，按类别组织。所有工具均接受可选的 `library` 参数（默认：`"user"`）。群组文献库使用 `"group:<id>"`。

## 读取工具

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `search` | 按标题、作者、标签、全文搜索；`ranked=True` 返回相关度排序结果（评分 + 片段，无索引） | `query`, `collection?`, `item_type?`, `sort?`, `limit`, `ranked?` |
| `list_items` | 列出所有条目 | `item_type?`, `sort?`, `limit` |
| `read` | 读取条目详情 + 笔记 | `key`, `detail?` |
| `pdf` | 提取 PDF 文本 | `key`, `pages?` |
| `annotations` | 提取 PDF 标注 | `key` |
| `references` | 提取解析后的参考文献（需 GROBID 服务） | `key` |
| `tables` | 提取 PDF 表格（pdfplumber） | `key` |
| `summarize` | AI 结构化摘要 | `key` |
| `summarize_all` | 导出所有条目摘要 | `limit` |
| `export` | 导出引用 (bibtex/csl-json/ris) | `key`, `fmt?` |
| `cite` | 格式化引用 (apa/nature/vancouver) | `key`, `style?` |
| `relate` | 查找相关条目 | `key`, `limit?` |
| `recent` | 最近添加/修改的条目 | `days?`, `modified?`, `limit?` |
| `note_view` | 查看条目笔记（`standalone=True` 列出所有独立笔记） | `key`, `standalone?` |
| `tag_view` | 查看条目标签 | `key` |
| `find_orphans` | 查找本地缺失文件的附件 | `dead_only?` |
| `collection_list` | 列出所有集合 | — |
| `collection_items` | 集合中的条目 | `collection_key` |
| `duplicates` | 查找重复 | `strategy?`, `threshold?`, `limit?` |
| `stats` | 文献库统计 | — |
| `update_status` | 检查预印本发表状态 | `key?`, `collection?`, `limit?`, `apply?` |

## 写入工具

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `add` | 通过 DOI 或 URL 添加条目 | `doi?`, `url?` |
| `add_from_pdf` | 从本地 PDF 添加 | `file_path`, `doi_override?` |
| `delete` | 删除条目（移入回收站） | `keys` |
| `update` | 更新元数据 | `key`, `title?`, `date?`, `fields?` |
| `attach` | 上传附件 | `parent_key`, `file_path`, `via_bridge?` |
| `note_add` | 添加笔记（Markdown 自动转 HTML；传 `raw=True` 原样存储；`standalone=True` 创建独立笔记） | `key`, `content`, `raw?`, `standalone?` |
| `note_update` | 更新笔记（Markdown 自动转 HTML；传 `raw=True` 原样存储） | `note_key`, `content`, `raw?` |
| `tag_add` | 添加标签 | `keys`, `tags` |
| `tag_remove` | 删除标签 | `keys`, `tags` |
| `collection_create` | 创建集合 | `name`, `parent_key?` |
| `collection_move` | 移动条目到集合 | `item_key`, `collection_key` |
| `collection_remove` | 将条目从集合中移除（条目仍保留在文献库中） | `item_key`, `collection_key` |
| `collection_delete` | 删除集合 | `collection_key` |
| `collection_rename` | 重命名集合 | `collection_key`, `new_name` |
| `collection_reorganize` | 批量重组 | `plan` |
| `trash_list` | 列出回收站条目 | `limit?` |
| `trash_restore` | 从回收站恢复 | `key` |

## 排序检索工具

用任意 Zotero 集合限定检索范围 —— 通过上面的 `collection_*` 工具或在 Zotero 应用中管理成员。检索是无索引的：无需构建索引，结果始终最新。如果只需要排序后的结果列表（不含证据片段），使用 `search` 并设置 `ranked=True`。

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `ask` | 带引用键的证据包（元数据 + PDF 片段）及作答指引；由 Agent 综合答案 —— zot 不调用 LLM | `question`, `collection?`, `evidence_k?` |
