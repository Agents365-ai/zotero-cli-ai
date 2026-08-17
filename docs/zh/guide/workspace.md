# 工作区

工作区就是一个 Zotero 集合。zot 内部无需创建任何东西，也不在本地存储数据 —— 在 Zotero 应用（或通过 `zot collection *`）中维护集合成员，zot 实时查询。没有需要构建的索引，结果始终是最新的。

## 管理成员

在 Zotero 应用中整理论文，或使用 CLI：

```bash
zot collection list                        # 所有集合（名称 + 键）
zot collection items COLL_KEY              # 集合中的条目
zot collection create "LLM Safety"         # 创建集合（需要 API 密钥）
zot collection move ITEM_KEY COLL_KEY      # 将条目移入集合
zot collection rename COLL_KEY "New Name"  # 重命名
zot collection delete COLL_KEY             # 删除集合
zot collection reorganize plan.json        # 按 JSON 计划批量创建 + 移动
```

## 排序检索

`zot workspace query` 按与自然语言问题的相关度对论文排序：

```bash
zot workspace query "reward hacking methods"
zot workspace query "reward hacking methods" --workspace "LLM Safety"
zot workspace query "tumour immunity" --workspace "CR | HCC" --top-k 10
```

- `--workspace` 将检索限定在某个集合（名称或键）内。省略则检索整个文献库。
- `--top-k` 设置返回结果数量（默认：5）。

检索是无索引的：条目评分来自 Zotero 自己的全文索引表（与 Zotero 应用构建的是同一个索引）中的 idf 加权词项覆盖度，并通过倒数排名融合（RRF）与元数据匹配（标题/摘要/作者/标签/笔记）合并。刚加入集合的论文立刻就能被搜到。

JSON 输出：

```json
{
  "ok": true,
  "data": {
    "query": "reward hacking methods",
    "workspace": "LLM Safety",
    "results": [
      {
        "rank": 1,
        "score": 0.0328,
        "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 },
        "item_key": "ABC123",
        "title": "...",
        "creators": ["..."],
        "date": "2024",
        "snippet": "..."
      }
    ]
  }
}
```

## 证据包

`zot ask` 更进一步：排序之后，它会围绕查询词即时提取 PDF 片段（pdfium，带缓存），返回带引用键的证据包。zot 本身不调用 LLM —— 由调用的 Agent 基于证据综合出有依据的答案。

```bash
zot ask "how does attention scale?"
zot ask "what dataset was used?" --workspace papers --evidence-k 8
```

- `--workspace` 将检索限定在某个集合（名称或键）内。省略则检索整个文献库。
- `--evidence-k` 设置证据条目数量（默认：12）。

JSON 输出：

```json
{
  "ok": true,
  "data": {
    "question": "what dataset was used?",
    "workspace": "papers",
    "mode": "index-free",
    "evidence": [
      { "cite_key": "ABC123", "source": "metadata", "text": "Title: ...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } },
      { "cite_key": "ABC123", "source": "pdf", "text": "...围绕查询词的片段...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } }
    ],
    "answer_instructions": "Answer the question using ONLY the evidence below. Cite each claim with its cite_key in parentheses, e.g. (ABCD1234). ..."
  }
}
```

## 从旧版本迁移

早期版本在 `~/.config/zot/workspaces/` 下保存本地工作区（JSON 文件加 `*.idx.sqlite` BM25/embedding 索引），并提供独立的子命令（`workspace new/add/remove/list/show/export/import/search/index/delete`）以及可选的 embedding 提供商（`config.toml` 中的 `[embedding]` 配置段、`ZOT_EMBEDDING_*` 环境变量）。这些已全部移除 —— 旧文件不再使用，可以删除。

迁移方法：把原来的论文集合重建为 Zotero 集合（在应用中操作，或用 `zot collection create` + `zot collection move`），然后按上文使用 `zot workspace query` / `zot ask`，无需任何索引步骤。
