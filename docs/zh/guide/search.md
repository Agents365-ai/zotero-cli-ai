# 搜索与浏览

## 搜索原理

`zot search` 在四个层面进行关键词匹配：

1. **标题与摘要** — 直接文本匹配
2. **作者姓名** — 姓和名匹配
3. **标签** — 精确标签匹配
4. **PDF 全文索引** — Zotero 内置的全文索引

## 选择搜索命令

- **`zot search`** — 跨元数据和全文索引的快速关键词查找（本页内容）。
- **`zot search --ranked`** — 对自然语言问题进行排序深度检索：返回相关度评分与片段，可限定在某个集合内。无索引：结果始终最新。
- **`zot ask`** — 同样的排序检索，但返回带引用键的证据包（元数据 + PDF 片段），供 Agent 综合答案。

## 排序深度检索

```bash
zot search "RLHF reward hacking" --ranked
zot search "tumour immunity" --ranked --collection "CR | HCC" --limit 10
```

- `--collection` 将检索限定在某个集合（名称或键；嵌套集合按名称解析）内。省略则检索整个文献库。
- `--limit` 设置返回结果数量。`--ranked` 会忽略 `--sort`/`--type`/`--stream`。

检索是无索引的：条目评分来自 Zotero 自己的全文索引表（与 Zotero 应用构建的是同一个索引）中的 idf 加权词项覆盖度，并通过倒数排名融合（RRF）与元数据匹配（标题/摘要/作者/标签/笔记）合并。刚加入的论文立刻就能被搜到。

JSON 输出：

```json
{
  "ok": true,
  "data": {
    "query": "reward hacking methods",
    "collection": "LLM Safety",
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
zot ask "what dataset was used?" --collection papers --evidence-k 8
```

- `--collection` 将检索限定在某个集合（名称或键）内。省略则检索整个文献库。
- `--evidence-k` 设置证据条目数量（默认：12）。

JSON 输出：

```json
{
  "ok": true,
  "data": {
    "question": "what dataset was used?",
    "collection": "papers",
    "mode": "index-free",
    "evidence": [
      { "cite_key": "ABC123", "source": "metadata", "text": "Title: ...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } },
      { "cite_key": "ABC123", "source": "pdf", "text": "...围绕查询词的片段...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } }
    ],
    "answer_instructions": "Answer the question using ONLY the evidence below. Cite each claim with its cite_key in parentheses, e.g. (ABCD1234). ..."
  }
}
```

## 使用集合限定范围

任何 Zotero 集合都可以用来限定排序检索或证据包的范围 —— zot 内部无需创建任何东西，也没有需要构建的索引。在 Zotero 应用中管理成员，或使用 CLI：

```bash
zot collection list                        # 所有集合（名称 + 键）
zot collection items COLL_KEY              # 集合中的条目
zot collection create "LLM Safety"         # 创建集合（需要 API 密钥）
zot collection move ITEM_KEY COLL_KEY      # 将条目移入集合
zot collection remove ITEM_KEY COLL_KEY    # 从集合中移除（条目仍保留在文献库中）
zot collection rename COLL_KEY "New Name"  # 重命名
zot collection delete COLL_KEY             # 删除集合
zot collection reorganize plan.json        # 按 JSON 计划批量创建 + 移动
```

!!! note "从 0.13 之前版本升级"
    `zot workspace` 命令组已在 0.13 中移除 —— 用 `zot search --ranked` 替代 `zot workspace query`，用 `zot ask --collection` 替代 `zot ask --workspace`。

## 基本搜索

```bash
zot search "transformer attention"
```

## 按集合过滤

```bash
zot search "BERT" --collection "NLP"
```

## 按条目类型过滤

```bash
zot search "protein" --type journalArticle
```

常用类型：`journalArticle`、`conferencePaper`、`preprint`、`book`、`bookSection`、`thesis`

## 排序结果

```bash
zot search "attention" --sort dateAdded --direction desc
zot search "attention" --sort title --direction asc
```

排序字段：`dateAdded`、`dateModified`、`title`、`creator`

## 列出所有条目

```bash
zot list --limit 20
zot list --collection "Machine Learning"
```

## 最近添加的条目

```bash
zot recent                    # 最近 7 天（默认）
zot recent --days 30          # 最近 30 天
zot recent --days 7 --modified  # 最近修改的
```

## 查看条目详情

```bash
zot read ABC123
```

显示元数据、摘要和笔记。使用 `--detail full` 查看所有字段。

## 查找相关条目

```bash
zot relate ABC123
```

查找共享标签、集合或显式关联的条目。

## 详情级别

```bash
zot --detail minimal search "attention"   # 仅显示键、标题、作者、年份
zot --detail standard read ABC123         # 默认 — 包含摘要、标签、DOI
zot --detail full read ABC123             # 所有字段，包括额外元数据
```

## JSON 输出

```bash
zot --json search "attention"
```

所有命令都支持 `--json` 获取机器可读输出。

## 文献库统计

```bash
zot stats
```

显示总条目数、PDF 数、笔记数、按类型分类、集合信息和热门标签。
