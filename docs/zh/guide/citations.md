# 引用与导出

## 导出引用

```bash
zot export ABC123                    # BibTeX（默认）
zot export ABC123 --format csl-json  # CSL-JSON
zot export ABC123 --format ris       # RIS
zot export ABC123 --format json      # 原始 JSON
```

## 格式化引用并复制到剪贴板

```bash
zot cite ABC123                      # APA（默认）
zot cite ABC123 --style nature       # Nature
zot cite ABC123 --style vancouver    # Vancouver
zot cite ABC123 --no-copy            # 仅打印，不复制
```

格式化后的引用会自动复制到剪贴板。

## 支持的引用格式

| 格式 | 样式 |
|------|------|
| **APA**（默认） | Author, A. B. (Year). Title. *Journal*, Volume(Issue), Pages. |
| **Nature** | Author, A. B. Title. *Journal* **Volume**, Pages (Year). |
| **Vancouver** | Author AB. Title. Journal. Year;Volume(Issue):Pages. |

## 批量导出

`zot export` 一次只接受一个条目键。要导出某个集合中的所有论文，可遍历 `zot collection items`：

```bash
zot --json collection items COLL_KEY | jq -r '.data[].key' | while read -r key; do
  zot export "$key"
done
```
