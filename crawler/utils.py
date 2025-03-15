"""
ページ取得モジュール
"""

from urllib.parse import urljoin, urlparse, urlunparse


def normalize_url(url):
    """URLからクエリパラメータとフラグメントを削除して正規化"""
    parsed_url = urlparse(url)
    # URLパスの末尾のスラッシュを統一する
    path = parsed_url.path
    if not path:
        path = "/"
    elif path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((parsed_url.scheme, parsed_url.netloc, path, "", "", ""))


def is_same_domain(url, domain):
    """URLが指定ドメインと同じかどうかを確認"""
    return domain in urlparse(url).netloc


def join_url(base, relative):
    """相対URLを絶対URLに変換"""
    return urljoin(base, relative)


def get_url_info(parsed_url):
    """パースされたURLからスキーム、ドメイン、パスを取得"""
    return {
        "scheme": parsed_url.scheme,
        "domain": parsed_url.netloc,
        "path": parsed_url.path,
    }
