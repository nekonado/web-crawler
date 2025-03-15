"""
ページ取得モジュール
"""

import requests
import time
from urllib import robotparser
from .config import MAX_RETRIES, DELAY_BETWEEN_REQUESTS


class WebFetcher:
    """Webページを取得するクラス"""

    def __init__(self, user_agent, use_robots_txt, logger):
        """フェッチャーの初期化"""
        self.user_agent = user_agent
        self.use_robots_txt = use_robots_txt
        self.headers = {"User-Agent": user_agent}
        self.logger = logger
        self.robot_parsers = {}  # ドメインごとにrobot.txtパーサーを保持

    def _get_robot_parser(self, url):
        """URLのドメインに対応するrobot.txtパーサーを取得または作成"""
        parsed_url = requests.utils.urlparse(url)
        domain = parsed_url.netloc

        if domain not in self.robot_parsers:
            parser = robotparser.RobotFileParser()
            robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
            try:
                parser.set_url(robots_url)
                parser.read()
                self.logger.info(f"robots.txtを読み込みました: {robots_url}")
                self.robot_parsers[domain] = parser
            except Exception as e:
                self.logger.warning(f"robots.txtの読み込みに失敗しました: {e}")
                self.robot_parsers[domain] = None

        return self.robot_parsers.get(domain)

    def can_fetch(self, url):
        """robots.txtに基づいてURLのクロールが許可されているか確認"""
        if not self.use_robots_txt:
            return True

        parser = self._get_robot_parser(url)
        if parser is None:
            return True

        return parser.can_fetch(self.user_agent, url)

    def fetch_page(self, url, retries=MAX_RETRIES):
        """ページを取得してレスポンスを返す、失敗した場合はNoneを返す"""
        # robots.txtをチェック
        if not self.can_fetch(url):
            self.logger.info(f"robots.txtによりアクセス禁止: {url}")
            return None

        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            if retries > 0:
                self.logger.warning(
                    f"再試行中 {url} ({MAX_RETRIES - retries + 1}/{MAX_RETRIES}): {e}"
                )
                time.sleep(DELAY_BETWEEN_REQUESTS)
                return self.fetch_page(url, retries - 1)
            else:
                self.logger.error(f"取得失敗 {url}: {e}")
                return None
