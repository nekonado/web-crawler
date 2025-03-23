/**
 * GitHub PagesからCSVデータを取得して2つのスプレッドシートに格納するスクリプト
 */
function fetchCSVFromDynamicGitHubPages() {
  // インデックスJSONのURLを設定（固定URL）
  const indexUrl = "https://nekonado.github.io/web-crawler/index.json";

  try {
    // まずインデックスJSONを取得して現在のパスを取得
    const indexResponse = UrlFetchApp.fetch(indexUrl);
    const indexData = JSON.parse(indexResponse.getContentText());
    const currentPath = indexData.current_path;

    // 取得したパスを使ってCSVのURLを構築
    const csvUrl = `https://nekonado.github.io/web-crawler/${currentPath}/data.csv`;

    // CSVデータを取得
    const csvResponse = UrlFetchApp.fetch(csvUrl);
    const csvContent = csvResponse.getContentText();

    // CSVデータをパース
    const csvData = Utilities.parseCsv(csvContent);

    // 現在のスプレッドシートを更新
    updateCurrentSpreadsheet(csvData);

    // 履歴スプレッドシートを更新
    updateHistorySpreadsheet(csvData, indexData.updated_at);

    // 更新情報を記録
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const timestampSheet = ss.getSheetByName("更新履歴") || ss.insertSheet("更新履歴");
    timestampSheet.appendRow([
      new Date(),
      "更新成功",
      `パス: ${currentPath}`,
      `最終更新: ${indexData.updated_at}`
    ]);

    Logger.log("CSVデータの取得と書き込みが正常に完了しました");
  } catch (e) {
    Logger.log("エラー発生: " + e.toString());
    // エラーログ
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const timestampSheet = ss.getSheetByName("更新履歴") || ss.insertSheet("更新履歴");
    timestampSheet.appendRow([new Date(), "エラー: " + e.toString()]);
  }
}

/**
 * 現在のスプレッドシートのlatestシートを更新する関数
 */

function updateCurrentSpreadsheet(csvData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("latest") || ss.insertSheet("latest");

  // シートをクリアして新しいデータを書き込み
  sheet.clear();
  sheet.getRange(1, 1, csvData.length, csvData[0].length).setValues(csvData);

  // ヘッダー行（1行目）の書式設定 - 背景色: #333、文字色: #fff
  sheet.getRange(1, 1, 1, csvData[0].length)
    .setBackground("#333333")
    .setFontColor("#ffffff")
    .setFontWeight("bold");

  // タイムスタンプを追加
  const timestampSheet = ss.getSheetByName("更新履歴") || ss.insertSheet("更新履歴");
  timestampSheet.appendRow([new Date(), "更新成功"]);
}

/**
 * 履歴スプレッドシートに新しいシートを作成して更新する関数
 */
function updateHistorySpreadsheet(csvData, updatedAt) {
  // 履歴スプレッドシートのIDを取得
  const historySpreadsheetId = getHistorySpreadsheetId();

  // 履歴スプレッドシートが見つからない場合は作成
  let historySpreadsheet;
  try {
    historySpreadsheet = SpreadsheetApp.openById(historySpreadsheetId);
  } catch (e) {
    // スプレッドシートが見つからない場合は新規作成
    historySpreadsheet = createHistorySpreadsheet();
  }

  // タイムスタンプ形式のシート名を作成（yyyymmddHHMM）
  const now = new Date();
  const sheetName = Utilities.formatDate(now, "Asia/Tokyo", "yyyyMMddHHmm");

  // 既存のシートを確認し、同名のシートがあれば削除して再作成
  try {
    const existingSheet = historySpreadsheet.getSheetByName(sheetName);
    if (existingSheet) {
      historySpreadsheet.deleteSheet(existingSheet);
    }

    // 新しいシートを作成
    const newSheet = historySpreadsheet.insertSheet(sheetName);

    // CSVデータを書き込み
    newSheet.getRange(1, 1, csvData.length, csvData[0].length).setValues(csvData);

    // 日時と説明を追加（シートの左上に）
    newSheet.getRange(1, csvData[0].length + 2).setValue("クロール実行日時:");
    newSheet.getRange(1, csvData[0].length + 3).setValue(now).setNumberFormat("yyyy/MM/dd HH:mm:ss");

    // 元データの更新日時も追加
    newSheet.getRange(2, csvData[0].length + 2).setValue("データ更新日時:");
    newSheet.getRange(2, csvData[0].length + 3).setValue(updatedAt);

    Logger.log("履歴スプレッドシートにシート「" + sheetName + "」を追加しました");

    // インデックスシートを自動的に更新
    updateHistoryIndex(historySpreadsheet);
  } catch (e) {
    Logger.log("履歴スプレッドシートの更新中にエラーが発生しました: " + e.toString());
    throw e;
  }
}

/**
 * 履歴スプレッドシートのIDを取得する関数
 * この関数は実際の環境に合わせて修正する必要があります
 */
function getHistorySpreadsheetId() {
  const historySpreadsheetName = "history";

  // 現在のスプレッドシートと同じフォルダにあるhistoryスプレッドシートを探す
  const currentSS = SpreadsheetApp.getActiveSpreadsheet();
  const currentSSFile = DriveApp.getFileById(currentSS.getId());
  const parentFolders = currentSSFile.getParents();

  if (parentFolders.hasNext()) {
    const parentFolder = parentFolders.next();
    const files = parentFolder.getFilesByName(historySpreadsheetName);

    if (files.hasNext()) {
      return files.next().getId();
    }
  }

  // 見つからない場合はnullを返す
  return null;
}

/**
 * 履歴スプレッドシートを新規作成する関数
 */
function createHistorySpreadsheet() {
  const historySpreadsheetName = "history";

  // 現在のスプレッドシートと同じフォルダに履歴スプレッドシートを作成
  const currentSS = SpreadsheetApp.getActiveSpreadsheet();
  const currentSSFile = DriveApp.getFileById(currentSS.getId());
  const parentFolders = currentSSFile.getParents();

  if (parentFolders.hasNext()) {
    const parentFolder = parentFolders.next();
    const newSS = SpreadsheetApp.create(historySpreadsheetName);
    const newSSFile = DriveApp.getFileById(newSS.getId());

    // 新しいファイルを同じフォルダに移動
    const currentFolder = newSSFile.getParents().next();
    parentFolder.addFile(newSSFile);
    currentFolder.removeFile(newSSFile);

    // インデックスシートを作成
    const indexSheet = newSS.getSheets()[0];
    indexSheet.setName("インデックス");
    setupIndexSheet(indexSheet);

    Logger.log("履歴スプレッドシート「" + historySpreadsheetName + "」を作成しました");
    return newSS;
  }

  throw new Error("履歴スプレッドシートを作成できませんでした");
}

/**
 * インデックスシートの初期設定を行う関数
 */
function setupIndexSheet(indexSheet) {
  // ヘッダーを設定
  indexSheet.getRange("A1").setValue("SEOクロール履歴一覧").setFontWeight("bold").setFontSize(14);
  indexSheet.getRange("A3:C3").setValues([["シート名", "実行日時", "アクション"]]).setFontWeight("bold");

  // ヘッダー行を固定
  indexSheet.setFrozenRows(3);

  // 列幅を調整
  indexSheet.setColumnWidth(1, 150);  // シート名
  indexSheet.setColumnWidth(2, 200);  // 実行日時
  indexSheet.setColumnWidth(3, 100);  // アクション

  // インデックスシートの体裁を整える
  indexSheet.getRange("A1:C1").merge();
  indexSheet.getRange("A3:C3").setBackground("#f3f3f3");

  // インデックスシートの説明を追加
  indexSheet.getRange("A2").setValue("各シートは実行日時（yyyyMMddHHmm形式）で命名されています。");
}

/**
 * インデックスシートを更新する関数
 * 各履歴シートへのリンクも作成する
 */
function updateHistoryIndex(historySpreadsheet) {
  if (!historySpreadsheet) {
    const historySpreadsheetId = getHistorySpreadsheetId();
    if (!historySpreadsheetId) return;
    historySpreadsheet = SpreadsheetApp.openById(historySpreadsheetId);
  }

  const indexSheet = historySpreadsheet.getSheetByName("インデックス");
  if (!indexSheet) return;

  // 既存のデータをクリア（ヘッダー以外）
  const lastRow = indexSheet.getLastRow();
  if (lastRow > 3) {
    indexSheet.getRange(4, 1, lastRow - 3, 3).clearContent();
  }

  // すべてのシートをインデックスに追加
  const sheets = historySpreadsheet.getSheets();
  let indexData = [];

  for (let i = 0; i < sheets.length; i++) {
    const sheet = sheets[i];
    const sheetName = sheet.getName();

    // インデックスシート自体は除外
    if (sheetName === "インデックス") continue;

    // シート名と日時の解析
    let dateValue;
    try {
      // シート名がyyyyMMddHHmm形式と仮定
      const year = parseInt(sheetName.substring(0, 4));
      const month = parseInt(sheetName.substring(4, 6)) - 1; // JavaScriptの月は0-11
      const day = parseInt(sheetName.substring(6, 8));
      const hour = parseInt(sheetName.substring(8, 10));
      const minute = parseInt(sheetName.substring(10, 12));

      dateValue = new Date(year, month, day, hour, minute);
    } catch (e) {
      dateValue = new Date(); // パースに失敗した場合は現在の日時
    }

    // データを配列に追加
    indexData.push([sheetName, dateValue]);
  }

  // 日時の新しい順にソート
  indexData.sort((a, b) => b[1] - a[1]);

  // インデックスに追加
  if (indexData.length > 0) {
    for (let i = 0; i < indexData.length; i++) {
      const row = i + 4; // ヘッダーが3行目まであるため
      const sheetName = indexData[i][0];
      const dateValue = indexData[i][1];

      // シート名を設定
      indexSheet.getRange(row, 1).setValue(sheetName);
      // 日時を設定
      indexSheet.getRange(row, 2).setValue(dateValue).setNumberFormat("yyyy/MM/dd HH:mm:ss");

      // リンクボタンを作成
      const linkFormula = '=HYPERLINK("#gid=' + historySpreadsheet.getSheetByName(sheetName).getSheetId() + '","表示")';
      indexSheet.getRange(row, 3).setFormula(linkFormula);
    }
  }
}

/**
 * 手動でインデックスを更新する関数（必要に応じて実行）
 */
function refreshHistoryIndex() {
  const historySpreadsheetId = getHistorySpreadsheetId();
  if (!historySpreadsheetId) {
    Logger.log("履歴スプレッドシートが見つかりません");
    return;
  }

  const historySpreadsheet = SpreadsheetApp.openById(historySpreadsheetId);
  updateHistoryIndex(historySpreadsheet);
  Logger.log("インデックスを更新しました");
}

/**
 * 定期実行のトリガーを設定する関数
 */
function setTrigger() {
  // 既存のトリガーをすべて削除
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'fetchCSVFromDynamicGitHubPages') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }

  // 毎週月曜の午前5時に実行するトリガーを設定
  ScriptApp.newTrigger('fetchCSVFromDynamicGitHubPages')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(5)
    .create();

  Logger.log("トリガーが設定されました");
}


/**
 * テスト用の手動実行関数
 */
function runTest() {
  fetchCSVFromDynamicGitHubPages();
}

/**
 * テスト用の手動関数 - historyスプレッドシートのみインデックス更新
 */
function runIndexUpdate() {
  refreshHistoryIndex();
}