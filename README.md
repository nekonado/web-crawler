# Web Crawler プロジェクト

このプロジェクトは指定した Web サイトを定期的にクロールし、サイト内のページ情報（タイトル、H1 タグ、メタディスクリプションなど）を収集するツールです。収集データは CSV として保存され、GitHub Gist にアップロードされ、さらに Google Spreadsheet でも閲覧できるようになっています。

## 機能概要

- 指定 URL からサイト内のページを自動的にクロール
- ページのタイトル、H1、メタディスクリプション、canonical URL などを収集
- マルチスレッド処理によるクロール速度の最適化
- robots.txt の尊重（設定可能）
- クロール結果を CSV で保存
- GitHub Actions による定期実行と Gist への自動アップロード
- Google Apps Script による Gist データの Spreadsheet インポート

## システム要件

- Python 3.9 以上
- Docker (ローカル実行用)
- GitHub アカウント (Actions と Gist の利用)
- Google アカウント (Spreadsheet と Apps Script の利用)

## セットアップ方法

### ローカル環境での実行

1. リポジトリをクローン

   ```
   git clone <リポジトリURL>
   cd <リポジトリ名>
   ```

2. 設定ファイルの準備

   ```
   cp config.sample.json config.json
   ```

3. `config.json` を編集してクロール設定を調整

   ```json
   {
     "start_url": "https://example.com/",
     "user_agent": "Mozilla/5.0 (compatible; MyCrawler/1.0; +http://example.com)",
     "use_robots_txt": true
   }
   ```

4. Docker を使った実行
   ```
   ./crawler.sh
   ```
   または Python を直接使う場合
   ```
   pip install -r requirements.txt
   python crawler.py
   ```

## クローラーのアーキテクチャ

クローラーは以下の主要コンポーネントで構成されています：

### 1. WebCrawler (crawler.py)

メインの制御クラスで、以下の役割を担います：

- クロールプロセス全体の管理
- 並行処理によるページ取得と処理の効率化
- URL キューの管理と訪問済み URL の追跡

クロールプロセスは以下の流れで動作します：

1. 開始 URL をキューに追加
2. スレッドプールを使って並行処理
3. 各 URL からページを取得、情報を抽出、新しいリンクを発見
4. 新しい URL をキューに追加して繰り返し

```python
# クロールの主要ロジック（簡略版）
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    # URL取得用のフューチャー
    link_futures = {
        executor.submit(self.get_all_links, url, depth, url_count): (url, depth)
        for url, depth in current_batch
    }

    # ページ処理用のフューチャー
    process_futures = {
        executor.submit(self.fetch_and_process_page, url, depth): (url, depth)
        for url, depth in current_batch
    }
```

### 2. WebFetcher (crawler/fetcher.py)

ページ取得を担当するコンポーネントです：

- HTTP リクエストの実行と応答の処理
- robots.txt の取得と解析
- エラー処理とリトライロジック

特徴：

- ドメインごとに robots.txt をキャッシュして再利用
- 接続エラー時でもクロールプロセスを継続できるよう堅牢に設計

### 3. PageParser (crawler/parser.py)

HTML 解析とデータ抽出を行います：

- BeautifulSoup を使用した HTML パース
- リンクの抽出と正規化
- 指定したページ情報（タイトル、H1、メタディスクリプションなど）の抽出

### 4. DataRecorder (crawler/recorder.py)

クロール結果の記録を担当します：

- 一時ファイルへのデータ書き込み
- 最終的な CSV ファイルの生成（URL でソート）
- 最新データの別ファイル（latest）への複製

## GitHub Actions によるクロールの自動化

このプロジェクトは GitHub Actions を使用して定期的なクロールを自動化しています。

### セットアップ手順

1. リポジトリをあなたの GitHub アカウントにフォーク/作成します

2. リポジトリの Settings → Secrets → Actions で以下のシークレットを追加：
   - `GIST_TOKEN`: GitHub のパーソナルアクセストークン（Gist 権限を持つもの）
   - `GIST_ID`: アップロード先の Gist ID
3. パーソナルアクセストークンの作成方法：

   - GitHub の Settings → Developer settings → Personal access tokens
   - 「Generate new token」をクリック
   - 少なくとも `gist` スコープにチェックを入れる
   - トークンを生成し、`GIST_TOKEN` として保存

4. Gist の作成方法：
   - https://gist.github.com/ にアクセス
   - 新しい Gist を作成（内容は一時的なもので良い）
   - 作成後の URL から Gist ID を取得 (例: `https://gist.github.com/username/abcdef1234567890` の `abcdef1234567890` 部分)
   - この ID を `GIST_ID` として保存

ワークフローは `.github/workflows/scheduled-crawler.yml` に定義されており、毎週日曜日 UTC 18:00（日本時間で月曜日午前 3 時）に実行されるよう設定されています。手動で実行する場合は、GitHub リポジトリの Actions タブから「Run workflow」を選択できます。

## Google Spreadsheet との連携

クロール結果を Google Spreadsheet で閲覧するための設定：

1. 新しい Google Spreadsheet を作成

2. メニューから「拡張機能」→「Apps Script」を開く

3. `gas/csvGistFetcher.js` の内容をコピーし、Gist URL を自分のものに書き換え：

   ```javascript
   const gistUrl =
     "https://gist.githubusercontent.com/あなたのユーザー名/あなたのGistID/raw/crawl_result_latest.csv";
   ```

4. Apps Script を保存して「実行」ボタンをクリック
   （初回は権限承認が必要）

5. 定期実行を設定する場合は `setTrigger()` 関数を実行

## クローラーの主な設定パラメータ

### config.json

- `start_url`: クロール開始 URL
- `user_agent`: クローラーの User-Agent
- `use_robots_txt`: robots.txt 尊重フラグ

### crawler/config.py の定数

- `MAX_RETRIES`: リクエスト再試行回数（デフォルト: 3）
- `DELAY_BETWEEN_REQUESTS`: リクエスト間隔（秒）（デフォルト: 1）
- `NUM_THREADS`: 並行スレッド数（デフォルト: 4）
- `MAX_URLS`: クロール最大 URL 数（デフォルト: 5000）
- `MAX_DEPTH`: クロール最大深さ（デフォルト: 10）

クロール量や速度を調整したい場合は、これらのパラメータを変更してください。

## プロジェクト構成

```
.
├── .github/workflows/    # GitHub Actions 設定
├── crawler/              # クローラーコアモジュール
│   ├── config.py         # 設定管理
│   ├── fetcher.py        # ページ取得モジュール
│   ├── parser.py         # HTML 解析モジュール
│   ├── recorder.py       # データ記録モジュール
│   └── utils.py          # ユーティリティ関数
├── gas/                  # Google Apps Script
├── output/               # 出力ディレクトリ
├── config.json           # プロジェクト設定
├── crawler.py            # メインスクリプト
└── Dockerfile            # Docker 環境設定
```

## ライセンス

MIT License

Copyright (c) 2024 Keisuke Ozeki
