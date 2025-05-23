"""
メインスクリプト
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from crawler.config import setup_logger, load_config, get_file_paths
from crawler.config import MAX_DEPTH, MAX_URLS, NUM_THREADS, DELAY_BETWEEN_REQUESTS
from crawler.fetcher import WebFetcher
from crawler.parser import PageParser
from crawler.recorder import DataRecorder
from crawler.utils import normalize_url


class WebCrawler:
    """Webクローラークラス - サイトのクロールと情報収集を行う"""

    def __init__(self, config):
        """クローラーの初期化"""
        # ロガーの設定
        self.logger = setup_logger()

        # 設定の読み込み
        self.start_url = config.get("start_url")
        self.user_agent = config.get("user_agent")
        self.use_robots_txt = config.get("use_robots_txt", False)
        self.domain = urlparse(self.start_url).netloc

        # ファイルパスの取得
        file_paths = get_file_paths()

        # コンポーネントの初期化
        self.fetcher = WebFetcher(self.user_agent, self.use_robots_txt, self.logger)
        self.parser = PageParser(self.logger)
        self.recorder = DataRecorder(
            file_paths["temp_file"], file_paths["final_file"], self.logger
        )

        # 訪問済みURLと参照元の追跡用データ構造
        self.visited = set()
        self.referrers = {}

    def get_all_links(self, url, depth, url_count):
        """ページから全ての有効なリンクを抽出して返す"""
        # 最大深さと最大URL数のチェック
        if depth > MAX_DEPTH or url_count >= MAX_URLS:
            return []

        response = self.fetcher.fetch_page(url)
        if not response:
            return []

        links = self.parser.extract_links(response.text, url, self.domain)
        result_links = []

        for link in links:
            # 未訪問のURLのみを追加
            if link not in self.visited and url_count < MAX_URLS:
                self.visited.add(link)
                self.referrers[link] = url
                result_links.append((link, depth + 1))
                url_count += 1

        return result_links

    def fetch_and_process_page(self, url, depth):
        """ページを取得して処理し、データを記録する"""
        response = self.fetcher.fetch_page(url)

        # レスポンスがNoneの場合（robots.txtによる禁止など）
        if response is None:
            return {
                "url": url,
                "status_code": 0,  # robots.txtによる禁止や他の理由でリクエストが行われなかった
                "title": "取得失敗",
                "h1": "取得失敗",
                "meta_description": "取得失敗",
                "referrer": self.referrers.get(url, "Direct Access"),
                "canonical_url": url,
                "depth": depth,
            }

        # 接続エラーの場合（DummyResponseのステータスコードは-1）
        if response.status_code == -1:
            return {
                "url": url,
                "status_code": -1,  # 接続エラーを示す特別なコード
                "title": "接続エラー",
                "h1": "接続エラー",
                "meta_description": "接続エラー",
                "referrer": self.referrers.get(url, "Direct Access"),
                "canonical_url": url,
                "depth": depth,
            }

        # HTTPレスポンスがある場合（200 OKもエラーステータスコードも含む）
        try:
            # ステータスコードが200以外の場合は簡略情報を返す
            if response.status_code != 200:
                return {
                    "url": url,
                    "status_code": response.status_code,  # 実際のHTTPステータスコード
                    "title": f"HTTPエラー {response.status_code}",
                    "h1": f"HTTPエラー {response.status_code}",
                    "meta_description": f"HTTPエラー {response.status_code}",
                    "referrer": self.referrers.get(url, "Direct Access"),
                    "canonical_url": url,
                    "depth": depth,
                }

            # コンテンツタイプをチェック
            content_type = response.headers.get("Content-Type", "").lower()
            if not (
                "text/html" in content_type or "application/xhtml+xml" in content_type
            ):
                return {
                    "url": url,
                    "status_code": response.status_code,
                    "title": f"非HTMLコンテンツ ({content_type})",
                    "h1": f"非HTMLコンテンツ",
                    "meta_description": f"コンテンツタイプ: {content_type}",
                    "referrer": self.referrers.get(url, "Direct Access"),
                    "canonical_url": url,
                    "depth": depth,
                }

            # 正常なレスポンス（200 OK）の場合は通常通り処理
            page_info = self.parser.extract_page_info(response.text, url)

            # レコードの作成
            record = {
                "url": url,
                "status_code": response.status_code,
                "title": page_info["title"],
                "h1": page_info["h1"],
                "meta_description": page_info["meta_description"],
                "referrer": self.referrers.get(url, "Direct Access"),
                "canonical_url": page_info["canonical_url"],
                "depth": depth,
            }

            return record
        except Exception as e:
            self.logger.error(f"ページ処理中のエラー {url}: {e}")
            return {
                "url": url,
                "status_code": response.status_code,  # エラーが発生しても実際のステータスコードを保持
                "title": "処理エラー",
                "h1": "処理エラー",
                "meta_description": "処理エラー",
                "referrer": self.referrers.get(url, "Direct Access"),
                "canonical_url": url,
                "depth": depth,
            }

    def crawl_website(self):
        """ウェブサイトをクローリングし、情報をCSVに保存"""
        self.logger.info(f"クロール開始: {self.start_url}")

        # 訪問予定URLとその深さを格納するキュー
        normalized_start_url = normalize_url(self.start_url)
        to_visit = [(normalized_start_url, 0)]  # (URL, 深さ)のタプル
        url_count = 0

        # 開始URLを訪問済みに追加
        self.visited.add(normalized_start_url)
        self.referrers[normalized_start_url] = "Direct Access"

        while to_visit and url_count < MAX_URLS:
            # 現在の訪問予定URLバッチ
            current_batch = to_visit[:NUM_THREADS]
            to_visit = to_visit[NUM_THREADS:]

            with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                # URL取得用のフューチャー
                link_futures = {
                    executor.submit(self.get_all_links, url, depth, url_count): (
                        url,
                        depth,
                    )
                    for url, depth in current_batch
                }

                # ページ処理用のフューチャー
                process_futures = {
                    executor.submit(self.fetch_and_process_page, url, depth): (
                        url,
                        depth,
                    )
                    for url, depth in current_batch
                }

                # 新しいリンクの処理
                for future in as_completed(link_futures):
                    current_url, depth = link_futures[future]
                    try:
                        links = future.result()
                        to_visit.extend(links)
                        url_count += len(links)
                        self.logger.info(
                            f"クロール中 ({depth}/{MAX_DEPTH}): {current_url} - {len(links)}リンク発見"
                        )
                    except Exception as e:
                        self.logger.error(f"リンク取得中のエラー {current_url}: {e}")

                # ページ処理結果の記録
                for future in as_completed(process_futures):
                    current_url, depth = process_futures[future]
                    try:
                        record = future.result()
                        self.recorder.write_record(record)
                    except Exception as e:
                        self.logger.error(f"ページ処理中のエラー {current_url}: {e}")

            # スレッドプールの実行後、少し待機
            time.sleep(DELAY_BETWEEN_REQUESTS)

        # 最終的なCSVファイルの作成（ソート済み）
        self.recorder.finalize()


def main():
    """メイン関数"""
    # ロガーの設定
    logger = setup_logger()

    # 環境変数からOUTPUT_DIRを取得
    output_dir = os.environ.get("OUTPUT_DIR", "output")

    # 出力ディレクトリの確認
    os.makedirs(output_dir, exist_ok=True)

    # 設定の読み込み
    config = load_config(logger)
    if not config:
        logger.error("設定ファイルがないか、読み込めませんでした。終了します。")
        exit(1)

    # クローラーの実行
    crawler = WebCrawler(config)
    crawler.crawl_website()


if __name__ == "__main__":
    main()
