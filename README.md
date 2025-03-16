# Web Crawler プロジェクト

このプロジェクトは、指定された Web サイトを定期的にクロールし、サイト内のページ情報（タイトル、H1 タグ、メタディスクリプションなど）を収集するツールです。収集データは CSV として保存され、GitHub Gist にアップロードされ、さらに Google Spreadsheet でも閲覧できるようになっています。

## 機能

- 指定された URL からサイト内のページを自動的にクロール
- ページのタイトル、H1 タグ、メタディスクリプション、canonical URL などを収集
- マルチスレッド処理によるクロール速度の最適化
- robots.txt の尊重（設定可能）
- クロール結果を CSV として保存
- GitHub Actions によるスケジュールされたクロールタスクと Gist への自動アップロード
- Google Apps Script による、Gist データを Google Spreadsheet に取り込む連携

## システム要件

- Python 3.9 以上
- Docker (ローカル実行用)
- GitHub Actions をサポートするリポジトリ (自動実行用)
- Google Apps Script (スプレッドシート連携用)

## セットアップ

### ローカル環境でのセットアップ

1. リポジトリのクローン:

   ```
   git clone <リポジトリURL>
   cd <リポジトリ名>
   ```

2. 設定ファイルの準備:
   ```
   cp config.sample.json config.json
   ```
3. `config.json`ファイルを編集して、クロールしたい URL とユーザーエージェントを設定:
   ```json
   {
     "start_url": "https://example.com/",
     "user_agent": "Mozilla/5.0 (compatible; MyCrawler/1.0; +http://example.com)",
     "use_robots_txt": true
   }
   ```

### 実行方法

#### Docker を使った実行

```
./crawler.sh
```

このスクリプトは、Docker コンテナを使ってクローラーを実行し、結果を`output/local/`ディレクトリに保存します。

#### Python を直接使った実行

1. 依存関係のインストール:

   ```
   pip install -r requirements.txt
   ```

2. クローラーの実行:
   ```
   python crawler.py
   ```

### GitHub Actions 設定

GitHub Actions により、毎週日曜日（日本時間で月曜日の午前 3 時）に自動的にクロールが実行されます。結果はリポジトリに保存され、設定された Gist にもアップロードされます。

1. GitHub リポジトリの「Settings」タブから「Secrets」を開き、以下のシークレットを追加:

   - `GIST_TOKEN`: GitHub のパーソナルアクセストークン（Gist の作成権限が必要）
   - `GIST_ID`: アップロード先の Gist ID

2. 手動でワークフローを実行する場合は、GitHub リポジトリの「Actions」タブから「Scheduled Web Crawler with Commit and Gist Upload」ワークフローを選択し、「Run workflow」をクリックします。

### Google Spreadsheet との連携

Google Apps Script を使用して、Gist から CSV データを取得し、スプレッドシートに反映します。

1. 新しい Google Spreadsheet を作成
2. ツール > スクリプトエディタを開く
3. `gas/csvGistFetcher.js`の内容をコピーし、Gist URL を適切に編集
4. スクリプトを保存して実行（初回は認証が必要）
5. スケジュール実行の設定（`setTrigger()`関数を実行）

## プロジェクト構成

```
.
├── .github/workflows/     # GitHub Actions設定
├── crawler/               # クローラーのコアモジュール
│   ├── __init__.py
│   ├── config.py          # 設定管理
│   ├── fetcher.py         # ページ取得モジュール
│   ├── parser.py          # HTML解析モジュール
│   ├── recorder.py        # データ記録モジュール
│   └── utils.py           # ユーティリティ関数
├── gas/                   # Google Apps Script
│   └── csvGistFetcher.js  # GistからCSV取得スクリプト
├── output/                # 出力ディレクトリ
│   ├── actions/           # GitHub Actions実行結果
│   └── local/             # ローカル実行結果
├── .gitignore
├── config.json            # プロジェクト設定
├── config.sample.json     # 設定サンプル
├── crawler.py             # メインスクリプト
├── crawler.sh             # Docker実行スクリプト
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile             # Dockerイメージ定義
└── requirements.txt       # Python依存関係
```

## 設定パラメータ

`config.json`で以下の項目を設定できます:

- `start_url`: クロールを開始する URL
- `user_agent`: クローラーのユーザーエージェント
- `use_robots_txt`: robots.txt を尊重するかどうか（true/false）

また、`crawler/config.py`で以下の定数を調整できます:

- `MAX_RETRIES`: リクエスト再試行の最大回数（デフォルト: 3）
- `DELAY_BETWEEN_REQUESTS`: リクエスト間の遅延時間（秒）（デフォルト: 1）
- `NUM_THREADS`: 並行スレッド数（デフォルト: 4）
- `MAX_URLS`: クロールする最大 URL 数（デフォルト: 5000）
- `MAX_DEPTH`: クロールする最大深さ（デフォルト: 10）

## 出力形式

クロール結果は以下の列を持つ CSV ファイルとして保存されます:

- `url`: クロールした URL
- `status_code`: HTTP ステータスコード
- `title`: ページタイトル
- `h1`: 最初の H1 タグの内容
- `meta_description`: メタディスクリプション
- `referrer`: この URL に到達した参照元 URL
- `canonical_url`: canonical URL
- `depth`: クロール開始点からの深さ

## ライセンス

MIT License

Copyright (c) 2024 Keisuke Ozeki
