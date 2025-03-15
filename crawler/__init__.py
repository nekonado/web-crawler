"""
初期化ファイル
"""

# クローラーパッケージの初期化
from .config import setup_logger, load_config, get_file_paths
from .fetcher import WebFetcher
from .parser import PageParser
from .recorder import DataRecorder
from .utils import normalize_url
