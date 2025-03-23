"""
HTML解析モジュール
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .utils import normalize_url, join_url, is_same_domain


class PageParser:
    """Webページの解析を行うクラス"""

    def __init__(self, logger):
        self.logger = logger
        # 無視すべきURLスキーム
        self.ignored_schemes = ["mailto:", "tel:", "javascript:", "file:"]
        # 無視すべきファイル拡張子
        self.ignored_extensions = [
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".avif",
            ".webp",
        ]

    def should_ignore_url(self, url):
        """無視すべきURLかどうかを判定"""
        # スキームのチェック
        for scheme in self.ignored_schemes:
            if url.lower().startswith(scheme):
                return True

        # 拡張子のチェック
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        for ext in self.ignored_extensions:
            if path.endswith(ext) or path.endswith(ext + "/"):
                return True

        # CDN-CGI パスのチェック (特定のCDNパスは無視)
        # 参考: https://developers.cloudflare.com/waf/tools/scrape-shield/email-address-obfuscation/
        if "/cdn-cgi/" in url.lower():
            return True

        return False

    def extract_links(self, html_content, base_url, domain):
        """ページからリンクを抽出して返す"""
        links = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                try:
                    href = a_tag.attrs["href"]
                    # 空のhrefは無視
                    if not href.strip():
                        continue

                    full_url = join_url(base_url, href)

                    # 無視すべきURLはスキップ
                    if self.should_ignore_url(full_url):
                        self.logger.debug(f"無視されたURL: {full_url}")
                        continue

                    normalized_url = normalize_url(full_url)

                    # 同じドメイン内のみ追加
                    if is_same_domain(normalized_url, domain):
                        links.append(normalized_url)
                except Exception as e:
                    self.logger.warning(f"リンク処理中のエラー: {e}")
        except Exception as e:
            self.logger.error(f"ページの解析中にエラーが発生しました {base_url}: {e}")

        return links

    def extract_page_info(self, html_content, url):
        """ページから情報を抽出（タイトル、H1、メタディスクリプション、正規URL）"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # タイトルの抽出
            title_tag = soup.title
            title = (
                title_tag.string.strip()
                if title_tag and title_tag.string
                else "タイトルなし"
            )

            # H1の抽出
            h1_tag = soup.find("h1")
            h1 = h1_tag.get_text().strip() if h1_tag else "H1なし"

            # メタディスクリプションの抽出
            meta_description = "説明なし"
            meta_desc_tag = soup.find("meta", attrs={"name": "description"})
            if meta_desc_tag and meta_desc_tag.get("content"):
                meta_description = meta_desc_tag["content"].strip()

            # canonical URLの抽出
            canonical_url = url  # デフォルトは現在のURL
            canonical_tag = soup.find("link", attrs={"rel": "canonical"})
            if canonical_tag and canonical_tag.get("href"):
                canonical_url = join_url(url, canonical_tag["href"])

            return {
                "title": title,
                "h1": h1,
                "meta_description": meta_description,
                "canonical_url": canonical_url,
            }
        except Exception as e:
            self.logger.error(f"情報抽出中のエラー {url}: {e}")
            return {
                "title": "情報抽出エラー",
                "h1": "情報抽出エラー",
                "meta_description": "情報抽出エラー",
                "canonical_url": url,
            }
