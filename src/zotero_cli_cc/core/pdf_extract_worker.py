"""Standalone PDF extraction worker process.

Usage: python -m zotero_cli_cc.core.pdf_extract_worker <pdf_path> [extractor]

Extracts the PDF's text (via the shared PdfCache) and prints it to stdout as
a JSON string. Runs detached from the caller's process so a native crash in
the pdfium C library (corrupt/hostile PDF) cannot take the CLI down; the
worker is not thread-safe, see commands/text.py for the pool design.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    pdf_path = Path(sys.argv[1])
    extractor_name = sys.argv[2] if len(sys.argv) > 2 else "pdfium"

    from zotero_cli_cc.core.pdf_cache import PdfCache
    from zotero_cli_cc.core.pdf_extractor import get_extractor

    cache = PdfCache()
    try:
        text = cache.get(pdf_path, extractor_name)
        if text is None:
            text = get_extractor(extractor_name).extract_text(pdf_path)
            cache.put(pdf_path, extractor_name, text)
    finally:
        cache.close()
    # JSON-encode so any control characters / long docs survive stdout intact.
    sys.stdout.write(json.dumps(text))


if __name__ == "__main__":
    main()
