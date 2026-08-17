"""zotero-cli-ai: Zotero CLI for any AI agent."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("zotero-cli-ai")
except PackageNotFoundError:  # running from a source tree without install
    __version__ = "0.0.0+unknown"
