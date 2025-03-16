"""
設定管理モジュール
"""

import json
import logging
import os
from datetime import datetime

# 定数
MAX_RETRIES = 3  # リクエスト再試行の最大回数
DELAY_BETWEEN_REQUESTS = 1  # リクエスト間の遅延（秒）
NUM_THREADS = 4  # 並行スレッド数
MAX_URLS = 5000  # クロールする最大URL数
MAX_DEPTH = 10  # クロールする最大深さ


# タイムスタンプの取得
def get_timestamp():
    return datetime.now().strftime("%Y%m%d")


# ファイルパスの設定
def get_file_paths():
    timestamp = get_timestamp()
    # 環境変数からOUTPUT_DIRを取得。設定されていない場合はデフォルトで"output"
    output_dir = os.environ.get("OUTPUT_DIR", "output")

    return {
        "temp_file": f"{output_dir}/temp_{timestamp}.csv",
        "final_file": f"{output_dir}/crawl_result_{timestamp}.csv",
        "log_file": f"{output_dir}/crawler_log_{timestamp}.log",
    }


# ロガーの設定
def setup_logger():
    file_paths = get_file_paths()
    log_file = file_paths["log_file"]

    # 出力ディレクトリの確認
    os.makedirs("output", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("web_crawler")


# 設定をJSONファイルから読み込む
def load_config(logger):
    """JSONファイルから設定を読み込む"""
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        return config
    except Exception as e:
        logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
        return None


# CSVのフィールド名定義
CSV_FIELDS = [
    "url",
    "status_code",
    "title",
    "h1",
    "meta_description",
    "referrer",
    "canonical_url",
    "depth",
]
