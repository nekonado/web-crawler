import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import logging
from datetime import datetime
from urllib import robotparser

# 定数
MAX_RETRIES = 3  # リクエスト再試行の最大回数
DELAY_BETWEEN_REQUESTS = 1  # リクエスト間の遅延（秒）
NUM_THREADS = 4  # 並行スレッド数
MAX_URLS = 5000  # クロールする最大URL数
MAX_DEPTH = 10  # クロールする最大深さ

# タイムスタンプとファイル名の設定
TIMESTAMP = datetime.now().strftime("%Y%m%d")
TEMP_FILE = f"output/temp_{TIMESTAMP}.csv"  # 一時出力ファイル
FINAL_FILE = f"output/crawl_result_{TIMESTAMP}.csv"  # 最終ソート済み出力ファイル
LOG_FILE = f"output/crawler_log_{TIMESTAMP}.log"  # ログファイル

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("web_crawler")


class WebCrawler:
    """Webクローラークラス - サイトのクロールと情報収集を行う"""

    def __init__(self, config):
        """クローラーの初期化"""
        self.start_url = config.get("start_url")
        self.user_agent = config.get("user_agent")
        self.use_robots_txt = config.get("use_robots_txt", False)
        self.headers = {"User-Agent": self.user_agent}
        self.domain = urlparse(self.start_url).netloc

        # 訪問済みURLと参照元の追跡用データ構造
        self.visited = set()
        self.referrers = {}

        # robots.txtのパーサー
        self.robot_parser = None
        if self.use_robots_txt:
            self._setup_robots_parser()

    def _setup_robots_parser(self):
        """robots.txtパーサーの設定"""
        self.robot_parser = robotparser.RobotFileParser()
        robots_url = f"{urlparse(self.start_url).scheme}://{self.domain}/robots.txt"
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            logger.info(f"robots.txtを読み込みました: {robots_url}")
        except Exception as e:
            logger.warning(f"robots.txtの読み込みに失敗しました: {e}")

    def can_fetch(self, url):
        """robots.txtに基づいてURLのクロールが許可されているか確認"""
        if not self.use_robots_txt or self.robot_parser is None:
            return True
        return self.robot_parser.can_fetch(self.user_agent, url)

    def fetch_page(self, url, retries=MAX_RETRIES):
        """ページを取得してレスポンスを返す、失敗した場合はNoneを返す"""
        # robots.txtをチェック
        if not self.can_fetch(url):
            logger.info(f"robots.txtによりアクセス禁止: {url}")
            return None

        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            if retries > 0:
                logger.warning(
                    f"再試行中 {url} ({MAX_RETRIES - retries + 1}/{MAX_RETRIES}): {e}"
                )
                time.sleep(DELAY_BETWEEN_REQUESTS)
                return self.fetch_page(url, retries - 1)
            else:
                logger.error(f"取得失敗 {url}: {e}")
                return None

    def normalize_url(self, url):
        """URLからクエリパラメータとフラグメントを削除して正規化"""
        parsed_url = urlparse(url)
        # URLパスの末尾のスラッシュを統一する（オプション）
        path = parsed_url.path
        if not path:
            path = "/"
        elif path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return urlunparse((parsed_url.scheme, parsed_url.netloc, path, "", "", ""))

    def get_all_links(self, url, depth, url_count):
        """ページから全ての有効なリンクを抽出して返す"""
        # 最大深さと最大URL数のチェック
        if depth > MAX_DEPTH or url_count >= MAX_URLS:
            return []

        response = self.fetch_page(url)
        if not response:
            return []

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            links = []

            for a_tag in soup.find_all("a", href=True):
                try:
                    href = a_tag.attrs["href"]
                    full_url = urljoin(url, href)
                    normalized_url = self.normalize_url(full_url)
                    parsed_url = urlparse(normalized_url)

                    # 同じドメイン内で未訪問のURLのみを追加
                    if (
                        self.domain in parsed_url.netloc
                        and normalized_url not in self.visited
                        and url_count < MAX_URLS
                    ):
                        self.visited.add(normalized_url)
                        self.referrers[normalized_url] = url
                        links.append((normalized_url, depth + 1))
                        url_count += 1
                except Exception as e:
                    logger.warning(f"リンク処理中のエラー: {e}")

            return links
        except Exception as e:
            logger.error(f"ページの解析中にエラーが発生しました {url}: {e}")
            return []

    def fetch_title_and_status(self, url):
        """URLのページタイトルとステータスコードを取得"""
        response = self.fetch_page(url)
        if not response:
            return "タイトル取得失敗", 0  # ステータスコードは数値0で統一

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            title_tag = soup.title
            title = (
                title_tag.string.strip()
                if title_tag and title_tag.string
                else "タイトルなし"
            )
            status_code = response.status_code
            return title, status_code
        except Exception as e:
            logger.error(f"タイトル取得中のエラー {url}: {e}")
            return "タイトル取得エラー", response.status_code

    def write_to_csv(self, file, data):
        """データをCSVファイルに書き込む"""
        try:
            with open(file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["url", "title", "status_code", "referrer", "depth"]
                )
                writer.writerow(data)
        except Exception as e:
            logger.error(f"CSV書き込み中のエラー: {e}")

    def crawl_website(self):
        """ウェブサイトをクローリングし、URL、タイトル、ステータスコード、参照元をCSVに保存"""
        logger.info(f"クロール開始: {self.start_url}")

        # 訪問予定URLとその深さを格納するキュー
        normalized_start_url = self.normalize_url(self.start_url)
        to_visit = [(normalized_start_url, 0)]  # (URL, 深さ)のタプル
        url_count = 0

        # 開始URLを訪問済みに追加
        self.visited.add(normalized_start_url)
        self.referrers[normalized_start_url] = "Direct Access"

        # 一時CSVファイルの作成とヘッダー書き込み
        try:
            with open(TEMP_FILE, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["url", "title", "status_code", "referrer", "depth"],
                )
                writer.writeheader()
        except Exception as e:
            logger.error(f"CSVファイル作成中のエラー: {e}")
            return

        while to_visit and url_count < MAX_URLS:
            # 現在の訪問予定URLバッチ
            current_batch = to_visit[:NUM_THREADS]
            to_visit = to_visit[NUM_THREADS:]

            with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                # URL取得用のフューチャー
                futures = {
                    executor.submit(self.get_all_links, url, depth, url_count): (
                        url,
                        depth,
                    )
                    for url, depth in current_batch
                }

                # タイトルとステータス取得用のフューチャー
                info_futures = {
                    executor.submit(self.fetch_title_and_status, url): (url, depth)
                    for url, depth in current_batch
                }

                # 新しいリンクの処理
                for future in as_completed(futures):
                    current_url, depth = futures[future]
                    try:
                        links = future.result()
                        to_visit.extend(links)
                        url_count += len(links)
                        logger.info(
                            f"クロール中 ({depth}/{MAX_DEPTH}): {current_url} - {len(links)}リンク発見"
                        )
                    except Exception as e:
                        logger.error(f"リンク取得中のエラー {current_url}: {e}")

                # タイトルとステータスの処理
                for future in as_completed(info_futures):
                    current_url, depth = info_futures[future]
                    try:
                        title, status_code = future.result()
                        referrer = self.referrers.get(current_url, "Direct Access")
                        self.write_to_csv(
                            TEMP_FILE,
                            {
                                "url": current_url,
                                "title": title,
                                "status_code": status_code,
                                "referrer": referrer,
                                "depth": depth,
                            },
                        )
                    except Exception as e:
                        logger.error(f"情報取得中のエラー {current_url}: {e}")

            # スレッドプールの実行後、少し待機
            time.sleep(DELAY_BETWEEN_REQUESTS)

        # 最終的なCSVファイルの作成（ソート済み）
        try:
            with open(TEMP_FILE, mode="r", encoding="utf-8") as infile, open(
                FINAL_FILE, mode="w", newline="", encoding="utf-8"
            ) as outfile:
                reader = csv.DictReader(infile)
                writer = csv.DictWriter(
                    outfile,
                    fieldnames=["url", "title", "status_code", "referrer", "depth"],
                )
                writer.writeheader()
                sorted_rows = sorted(reader, key=lambda row: row["url"])
                writer.writerows(sorted_rows)

            logger.info(f"クロール完了。結果は '{FINAL_FILE}' に保存されました。")
        except Exception as e:
            logger.error(f"最終CSVファイル作成中のエラー: {e}")


# 設定をJSONファイルから読み込む
def load_config():
    """JSONファイルから設定を読み込む"""
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        return config
    except Exception as e:
        logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
        return None


if __name__ == "__main__":
    # 出力ディレクトリの確認
    os.makedirs("output", exist_ok=True)

    # 設定の読み込み
    config = load_config()
    if not config:
        logger.error("設定ファイルがないか、読み込めませんでした。終了します。")
        exit(1)

    # クローラーの実行
    crawler = WebCrawler(config)
    crawler.crawl_website()
