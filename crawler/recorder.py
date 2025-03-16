"""
データ記録モジュール
"""

import csv
import os
import shutil
from .config import CSV_FIELDS


class DataRecorder:
    """クロール結果の記録を行うクラス"""

    def __init__(self, temp_file, final_file, logger):
        self.temp_file = temp_file
        self.final_file = final_file
        self.logger = logger

        # 一時ファイルの初期化
        self._initialize_csv(self.temp_file)

    def _initialize_csv(self, file_path):
        """CSVファイルの初期化とヘッダーの書き込み"""
        try:
            # 出力ディレクトリの確認
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
                writer.writeheader()
        except Exception as e:
            self.logger.error(f"CSVファイル作成中のエラー: {e}")
            raise

    def _escape_text_fields(self, data):
        """テキストフィールドの改行をエスケープ"""
        text_fields = ["title", "h1", "meta_description"]
        for field in text_fields:
            if field in data and data[field]:
                # 改行文字をエスケープ（\n -> \\n, \r -> \\r）
                data[field] = data[field].replace("\n", "\\n").replace("\r", "\\r")
        return data

    def write_record(self, data):
        """データをCSVファイルに書き込む"""
        try:
            # テキストフィールドの改行をエスケープ
            escaped_data = self._escape_text_fields(data)

            with open(self.temp_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
                writer.writerow(escaped_data)
        except Exception as e:
            self.logger.error(f"CSV書き込み中のエラー: {e}")

    def finalize(self):
        """一時ファイルを読み込み、ソートして最終ファイルに書き込む"""
        try:
            with open(self.temp_file, mode="r", encoding="utf-8") as infile, open(
                self.final_file, mode="w", newline="", encoding="utf-8"
            ) as outfile:
                reader = csv.DictReader(infile)
                writer = csv.DictWriter(outfile, fieldnames=CSV_FIELDS)
                writer.writeheader()

                # URLでソート
                sorted_rows = sorted(reader, key=lambda row: row["url"])
                writer.writerows(sorted_rows)

            # latest版を作成する場所を取得
            output_dir = os.path.dirname(os.path.dirname(self.final_file))
            latest_file = os.path.join(output_dir, "crawl_result_latest.csv")

            # 最終ファイルをlatestファイルにコピー
            shutil.copy2(self.final_file, latest_file)

            self.logger.info(
                f"クロール完了。結果は '{self.final_file}' に保存されました。"
            )
            return True
        except Exception as e:
            self.logger.error(f"最終CSVファイル作成中のエラー: {e}")
            return False
