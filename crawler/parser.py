"""
HTML解析モジュール
"""

from bs4 import BeautifulSoup
from .utils import normalize_url, join_url, is_same_domain


class PageParser:
    """Webページの解析を行うクラス"""

    def __init__(self, logger):
        self.logger = logger

    def extract_links(self, html_content, base_url, domain):
        """ページから全てのリンクを抽出"""
        links = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                try:
                    href = a_tag.attrs["href"]
                    full_url = join_url(base_url, href)
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
        """ページから情報を抽出（タイトル、メタディスクリプション、正規URL）"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # タイトルの抽出
            title_tag = soup.title
            title = (
                title_tag.string.strip()
                if title_tag and title_tag.string
                else "タイトルなし"
            )

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
                "meta_description": meta_description,
                "canonical_url": canonical_url,
            }
        except Exception as e:
            self.logger.error(f"情報抽出中のエラー {url}: {e}")
            return {
                "title": "情報抽出エラー",
                "meta_description": "情報抽出エラー",
                "canonical_url": url,
            }
