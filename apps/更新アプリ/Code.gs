/* ============================================================
   サイト更新アプリ（スマホからお知らせ・施工事例を入れる）

   ■ これは何をするもの？
     事務ご担当者様がスマホで
       ・写真をその場で撮る／選ぶ
       ・見出しや本文を入れる
       ・［保存］を押す
     だけで、
       1. 写真・チラシを共有フォルダ（ドライブ）に置き、
          「リンクを知っている全員が閲覧可」にする
       2. そのリンクを台帳（スプレッドシート）の行に書き込む
     までを自動で行います。
     あとは今までどおり、10分おきの自動反映
     （.github/workflows/news-from-sheet.yml）がサイトに出します。

   ■ 台帳との約束
     ・列は「1行目の見出しの名前」で探します。列の並び順は自由です。
       列名は tools/お知らせ台帳_生成.py・tools/施工事例台帳_生成.py と同じです。
     ・お知らせは「台帳の上から順」にサイトに並ぶので、新しい行は
       見出しのすぐ下（2行目）に差し込みます。
     ・施工事例は「表示順」の小さい順に並ぶので、行は下に足し、
       表示順の数字で先頭／最後を決めます。

   ■ 設定（スクリプト プロパティ）  ※手順は README.md
       NEWS_SHEET_ID      お知らせ台帳のスプレッドシートID（必須）
       NEWS_SHEET_NAME    お知らせ台帳のシート名（空なら列名から自動で探す）
       CASES_SHEET_ID     施工事例台帳のスプレッドシートID（空なら施工事例は使わない）
       CASES_SHEET_NAME   施工事例台帳のシート名（空なら列名から自動で探す）
       PHOTO_FOLDER_ID    写真・チラシを置く共有フォルダのID（必須）
   ============================================================ */

// ---- 台帳の列名（スプレッドシートの1行目と完全に一致させる） ----
var NEWS_COLS = {
  date: '掲載日',
  category: '種別',
  title: '見出し',
  body: '本文',
  until: '掲載終了日',
  publish: '公開',
  image: '写真',
  link: 'リンク',
  linkText: 'リンク文字',
  link2: 'リンク2',
  link2Text: 'リンク2文字',
  archive: '過去へ下げる'
};
var NEWS_REQUIRED = ['掲載日', '種別', '見出し', '公開'];

var CASE_COLS = {
  order: '表示順',
  category: '種別',
  type: '分類',
  location: '施工箇所',
  period: '工期',
  cost: '費用目安',
  building: '建物種別',
  problem: '工事前の悩み',
  work: '施工内容',
  change: '施工後の変化',
  comment: '担当者コメント',
  before: 'ビフォー写真',
  after: 'アフター写真',
  link: 'リンク',
  consent: '施主承諾',
  publish: '公開'
};
var CASE_REQUIRED = ['表示順', '種別', '分類', 'ビフォー写真', 'アフター写真', '施主承諾', '公開'];

// /works/ の絞り込み分類（tools/施工事例台帳_生成.py の TYPE_ORDER と同じ）
var CASE_TYPES = ['外壁塗装', '屋根・雨漏り', '水回り', '内装・建具', '外構・その他'];

// 台帳の「公開」などで「はい」とみなす書き方（生成スクリプトの TRUE_WORDS と同じ）
var TRUE_WORDS = ['true', '1', 'yes', 'y', 'はい', '○', '◯', '〇', '✓', '✔', 'レ', 'x', 'ｘ', '×'];

// 写真の取り込み側（tools/お知らせ写真_取り込み.py）が受け付ける上限と同じ
var MAX_FILE_BYTES = 20 * 1024 * 1024;

var IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
var FLYER_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp'];

// 「登録済み」の画面に出す件数
var RECENT_COUNT = 15;

var SITE_URL = 'https://marusho-iwaki.co.jp/';


// ============================================================
//  画面を出す
// ============================================================

function doGet() {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('まるしょう サイト更新')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}


// ============================================================
//  画面から呼ばれる関数（google.script.run）
// ============================================================

/** 最初に画面へ渡すもの：候補の一覧と、登録済みの行 */
function getInitialData() {
  var config = readConfig_();
  var news = openLedger_(config.newsSheetId, config.newsSheetName, NEWS_REQUIRED, 'お知らせ台帳');
  var result = {
    user: safeUserEmail_(),
    siteUrl: SITE_URL,
    news: {
      categories: distinctValues_(news, NEWS_COLS.category, ['お知らせ', 'キャンペーン', 'イベント']),
      recent: recentNews_(news)
    },
    cases: null
  };
  if (config.casesSheetId) {
    var cases = openLedger_(config.casesSheetId, config.casesSheetName, CASE_REQUIRED, '施工事例台帳');
    result.cases = {
      types: CASE_TYPES.slice(),
      buildings: distinctValues_(cases, CASE_COLS.building, ['戸建て']),
      recent: recentCases_(cases)
    };
  }
  return result;
}

/**
 * お知らせを1件、台帳の2行目に差し込む。
 * payload: { date, until, category, title, body, publish,
 *            photo: {name, type, data(base64)} | null,
 *            flyer: {name, type, data(base64)} | null, flyerText }
 */
function saveNews(payload) {
  var config = readConfig_();
  var item = validateNews_(payload);
  var created = [];
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var ledger = openLedger_(config.newsSheetId, config.newsSheetName, NEWS_REQUIRED, 'お知らせ台帳');
    var folder = openFolder_(config.photoFolderId);
    var stamp = item.date + '_' + shortName_(item.title);

    if (payload.photo) {
      item.image = uploadFile_(folder, payload.photo, IMAGE_TYPES, stamp + '_写真', created);
    }
    if (payload.flyer) {
      item.link = uploadFile_(folder, payload.flyer, FLYER_TYPES, stamp + '_チラシ', created);
      item.linkText = item.linkText || defaultFlyerText_(payload.flyer.type);
    }

    var values = {};
    values[NEWS_COLS.date] = item.date;
    values[NEWS_COLS.category] = item.category;
    values[NEWS_COLS.title] = item.title;
    values[NEWS_COLS.body] = item.body;
    values[NEWS_COLS.until] = item.until;
    values[NEWS_COLS.image] = item.image || '';
    values[NEWS_COLS.link] = item.link || '';
    values[NEWS_COLS.linkText] = item.linkText || '';
    values[NEWS_COLS.publish] = item.publish;

    var row = insertTopRow_(ledger.sheet);
    writeRow_(ledger, row, values);
    SpreadsheetApp.flush();
    return { row: row, message: item.publish
      ? '保存しました。10分ほどでサイトに出ます。'
      : '下書きとして保存しました（公開はしていません）。' };
  } catch (error) {
    trashAll_(created);
    throw error;
  } finally {
    lock.releaseLock();
  }
}

/**
 * 施工事例を1件、台帳の空いている行に書き込む。
 * payload: { position: 'first'|'last', category, type, location, period, cost,
 *            building, problem, work, change, comment, consent, publish,
 *            before: {name, type, data}, after: {name, type, data} }
 */
function saveCase(payload) {
  var config = readConfig_();
  if (!config.casesSheetId) {
    throw new Error('施工事例台帳がまだ設定されていません（CASES_SHEET_ID）。');
  }
  var item = validateCase_(payload);
  var created = [];
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var ledger = openLedger_(config.casesSheetId, config.casesSheetName, CASE_REQUIRED, '施工事例台帳');
    var folder = openFolder_(config.photoFolderId);
    var stamp = todayString_() + '_施工事例_' + shortName_(item.category);

    var beforeUrl = uploadFile_(folder, payload.before, IMAGE_TYPES, stamp + '_ビフォー', created);
    var afterUrl = uploadFile_(folder, payload.after, IMAGE_TYPES, stamp + '_アフター', created);

    var orders = columnValues_(ledger, CASE_COLS.order);
    var values = {};
    values[CASE_COLS.order] = nextOrder_(orders, item.position);
    values[CASE_COLS.category] = item.category;
    values[CASE_COLS.type] = item.type;
    values[CASE_COLS.location] = item.location;
    values[CASE_COLS.period] = item.period;
    values[CASE_COLS.cost] = item.cost;
    values[CASE_COLS.building] = item.building;
    values[CASE_COLS.problem] = item.problem;
    values[CASE_COLS.work] = item.work;
    values[CASE_COLS.change] = item.change;
    values[CASE_COLS.comment] = item.comment;
    values[CASE_COLS.before] = beforeUrl;
    values[CASE_COLS.after] = afterUrl;
    values[CASE_COLS.consent] = item.consent;
    values[CASE_COLS.publish] = item.publish;

    var row = findEmptyCaseRow_(ledger);
    writeRow_(ledger, row, values);
    SpreadsheetApp.flush();
    return { row: row, message: item.publish
      ? '保存しました。10分ほどでサイトに出ます。'
      : '下書きとして保存しました（公開はしていません）。' };
  } catch (error) {
    trashAll_(created);
    throw error;
  } finally {
    lock.releaseLock();
  }
}

/**
 * 登録済みの行の「公開」を切り替える。
 * 行がずれていたとき（誰かが台帳で行を足した等）に別の行を触らないよう、
 * 画面に出ていた見出しと台帳の見出しが一致するときだけ書き換える。
 */
function setPublish(kind, row, expectedTitle, publish) {
  var config = readConfig_();
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var ledger, titleCol;
    if (kind === 'news') {
      ledger = openLedger_(config.newsSheetId, config.newsSheetName, NEWS_REQUIRED, 'お知らせ台帳');
      titleCol = NEWS_COLS.title;
    } else if (kind === 'cases' && config.casesSheetId) {
      ledger = openLedger_(config.casesSheetId, config.casesSheetName, CASE_REQUIRED, '施工事例台帳');
      titleCol = CASE_COLS.category;
    } else {
      throw new Error('切り替える台帳が分かりませんでした。');
    }
    row = Number(row);
    if (!(row >= 2 && row <= ledger.sheet.getLastRow())) {
      throw new Error('行が見つかりませんでした。画面を読み込み直してください。');
    }
    var actual = String(ledger.sheet.getRange(row, ledger.index[titleCol]).getDisplayValue()).trim();
    if (actual !== String(expectedTitle || '').trim()) {
      throw new Error('台帳の行が動いていたため、書き換えを止めました。画面を読み込み直してください。');
    }
    if (kind === 'cases' && publish) {
      var consent = ledger.sheet.getRange(row, ledger.index[CASE_COLS.consent]).getDisplayValue();
      if (!isTrue_(consent)) {
        throw new Error('施主様の承諾が付いていないため公開できません。台帳の「施主承諾」を確認してください。');
      }
    }
    var values = {};
    values[kind === 'news' ? NEWS_COLS.publish : CASE_COLS.publish] = !!publish;
    writeRow_(ledger, row, values);
    SpreadsheetApp.flush();
    return { row: row, publish: !!publish };
  } finally {
    lock.releaseLock();
  }
}


// ============================================================
//  入力の確認（台帳を触る前に、ここで止める）
// ============================================================

function validateNews_(payload) {
  if (!payload) throw new Error('入力が空でした。');
  var item = {
    date: normalizeDate_(payload.date),
    until: payload.until ? normalizeDate_(payload.until) : '',
    category: clean_(payload.category) || 'お知らせ',
    title: clean_(payload.title),
    body: cleanMultiline_(payload.body),
    linkText: clean_(payload.flyerText),
    publish: !!payload.publish
  };
  if (!item.date) throw new Error('掲載日を入れてください。');
  if (payload.until && !item.until) throw new Error('掲載終了日の形が正しくありません。');
  if (!item.title) throw new Error('見出しを入れてください。');
  if (item.title.length > 80) throw new Error('見出しは80文字までにしてください。');
  if (item.until && item.until < item.date) throw new Error('掲載終了日が掲載日より前になっています。');
  return item;
}

function validateCase_(payload) {
  if (!payload) throw new Error('入力が空でした。');
  var item = {
    position: payload.position === 'last' ? 'last' : 'first',
    category: clean_(payload.category),
    type: clean_(payload.type),
    location: clean_(payload.location),
    period: clean_(payload.period),
    cost: clean_(payload.cost),
    building: clean_(payload.building),
    problem: cleanMultiline_(payload.problem),
    work: cleanMultiline_(payload.work),
    change: cleanMultiline_(payload.change),
    comment: cleanMultiline_(payload.comment),
    consent: !!payload.consent,
    publish: !!payload.publish
  };
  if (!item.category) throw new Error('工事の名前（種別）を入れてください。');
  if (CASE_TYPES.indexOf(item.type) < 0) throw new Error('分類を選んでください。');
  if (!payload.before) throw new Error('ビフォー写真を選んでください。');
  if (!payload.after) throw new Error('アフター写真を選んでください。');
  if (item.publish && !item.consent) {
    throw new Error('施主様の掲載承諾がないと公開できません。承諾がまだなら「下書き」で保存してください。');
  }
  return item;
}


// ============================================================
//  台帳を開く・読む・書く
// ============================================================

function readConfig_() {
  var props = PropertiesService.getScriptProperties();
  var config = {
    newsSheetId: clean_(props.getProperty('NEWS_SHEET_ID')),
    newsSheetName: clean_(props.getProperty('NEWS_SHEET_NAME')),
    casesSheetId: clean_(props.getProperty('CASES_SHEET_ID')),
    casesSheetName: clean_(props.getProperty('CASES_SHEET_NAME')),
    photoFolderId: clean_(props.getProperty('PHOTO_FOLDER_ID'))
  };
  if (!config.newsSheetId) throw new Error('設定が足りません：NEWS_SHEET_ID（お知らせ台帳）');
  if (!config.photoFolderId) throw new Error('設定が足りません：PHOTO_FOLDER_ID（写真の共有フォルダ）');
  return config;
}

/** 台帳を開き、列名→列番号（1始まり）の対応を作る */
function openLedger_(spreadsheetId, sheetName, required, label) {
  var book;
  try {
    book = SpreadsheetApp.openById(spreadsheetId);
  } catch (error) {
    throw new Error(label + 'を開けませんでした。編集できる権限があるか確認してください。');
  }
  var sheets = sheetName ? [book.getSheetByName(sheetName)] : book.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    var sheet = sheets[i];
    if (!sheet) continue;
    var index = headerIndex_(sheet);
    var missing = required.filter(function (name) { return !index[name]; });
    if (missing.length === 0) return { sheet: sheet, index: index };
    if (sheetName) {
      throw new Error(label + 'に必要な列がありません：' + missing.join('／'));
    }
  }
  throw new Error(label + (sheetName ? 'のシート「' + sheetName + '」が見つかりません。' : 'の見出しの行が見つかりません。'));
}

function headerIndex_(sheet) {
  var lastCol = sheet.getLastColumn();
  var index = {};
  if (lastCol < 1) return index;
  var headers = sheet.getRange(1, 1, 1, lastCol).getDisplayValues()[0];
  for (var c = 0; c < headers.length; c++) {
    var name = String(headers[c]).replace(/﻿/g, '').trim();
    if (name && !index[name]) index[name] = c + 1;
  }
  return index;
}

function columnValues_(ledger, name) {
  var col = ledger.index[name];
  var last = ledger.sheet.getLastRow();
  if (!col || last < 2) return [];
  return ledger.sheet.getRange(2, col, last - 1, 1).getDisplayValues().map(function (r) { return r[0]; });
}

function distinctValues_(ledger, name, defaults) {
  var seen = {};
  var out = [];
  defaults.concat(columnValues_(ledger, name)).forEach(function (value) {
    var v = clean_(value);
    if (v && !seen[v]) { seen[v] = true; out.push(v); }
  });
  return out;
}

/** 見出しの下（2行目）に1行差し込み、下の行の書式・チェックボックスを写す */
function insertTopRow_(sheet) {
  var lastCol = Math.max(sheet.getLastColumn(), 1);
  var hadData = sheet.getLastRow() >= 2;
  sheet.insertRowBefore(2);
  if (hadData) {
    var from = sheet.getRange(3, 1, 1, lastCol);
    var to = sheet.getRange(2, 1, 1, lastCol);
    from.copyTo(to, SpreadsheetApp.CopyPasteType.PASTE_FORMAT, false);
    from.copyTo(to, SpreadsheetApp.CopyPasteType.PASTE_DATA_VALIDATION, false);
  }
  return 2;
}

/** 施工事例：種別・ビフォー・アフターがすべて空の行を上から探す。無ければ最後の次 */
function findEmptyCaseRow_(ledger) {
  var sheet = ledger.sheet;
  var last = sheet.getLastRow();
  var cols = [CASE_COLS.category, CASE_COLS.before, CASE_COLS.after].map(function (n) { return ledger.index[n]; });
  if (last >= 2) {
    var width = sheet.getLastColumn();
    var data = sheet.getRange(2, 1, last - 1, width).getDisplayValues();
    for (var r = 0; r < data.length; r++) {
      var empty = cols.every(function (c) { return !String(data[r][c - 1]).trim(); });
      if (empty) return r + 2;
    }
  }
  var row = last + 1;
  if (last >= 2) {
    var lastCol = Math.max(sheet.getLastColumn(), 1);
    var from = sheet.getRange(last, 1, 1, lastCol);
    var to = sheet.getRange(row, 1, 1, lastCol);
    from.copyTo(to, SpreadsheetApp.CopyPasteType.PASTE_FORMAT, false);
    from.copyTo(to, SpreadsheetApp.CopyPasteType.PASTE_DATA_VALIDATION, false);
  }
  return row;
}

/**
 * 列名をキーにした値を、その行のセルに1つずつ書く（他の列には触らない）。
 * true/false は、チェックボックスの列ならそのまま、そうでなければ「○」／空にする。
 */
function writeRow_(ledger, row, values) {
  Object.keys(values).forEach(function (name) {
    var col = ledger.index[name];
    if (!col) return; // 台帳にない列（任意の列）は書かない
    var range = ledger.sheet.getRange(row, col);
    var value = values[name];
    if (typeof value === 'boolean') {
      value = isCheckbox_(range) ? value : (value ? '○' : '');
    } else if (typeof value === 'string' && /^[=+\-@]/.test(value) && !/^https?:\/\//.test(value)) {
      // 入力が数式として解釈されないようにする
      value = "'" + value;
    }
    range.setValue(value);
  });
}

function isCheckbox_(range) {
  var rule = range.getDataValidation();
  return !!rule && rule.getCriteriaType() === SpreadsheetApp.DataValidationCriteria.CHECKBOX;
}

function recentNews_(ledger) {
  var sheet = ledger.sheet;
  var last = sheet.getLastRow();
  if (last < 2) return [];
  var count = Math.min(RECENT_COUNT, last - 1);
  var data = sheet.getRange(2, 1, count, sheet.getLastColumn()).getDisplayValues();
  var pick = function (r, name) { return ledger.index[name] ? String(r[ledger.index[name] - 1]).trim() : ''; };
  return data.map(function (r, i) {
    return {
      row: i + 2,
      date: pick(r, NEWS_COLS.date),
      category: pick(r, NEWS_COLS.category),
      title: pick(r, NEWS_COLS.title),
      until: pick(r, NEWS_COLS.until),
      hasPhoto: !!pick(r, NEWS_COLS.image),
      publish: isTrue_(pick(r, NEWS_COLS.publish))
    };
  }).filter(function (it) { return it.title; });
}

function recentCases_(ledger) {
  var sheet = ledger.sheet;
  var last = sheet.getLastRow();
  if (last < 2) return [];
  var data = sheet.getRange(2, 1, last - 1, sheet.getLastColumn()).getDisplayValues();
  var pick = function (r, name) { return ledger.index[name] ? String(r[ledger.index[name] - 1]).trim() : ''; };
  var items = data.map(function (r, i) {
    return {
      row: i + 2,
      order: pick(r, CASE_COLS.order),
      title: pick(r, CASE_COLS.category),
      type: pick(r, CASE_COLS.type),
      consent: isTrue_(pick(r, CASE_COLS.consent)),
      publish: isTrue_(pick(r, CASE_COLS.publish))
    };
  }).filter(function (it) { return it.title; });
  items.sort(function (a, b) { return orderNumber_(a.order) - orderNumber_(b.order); });
  return items.slice(0, RECENT_COUNT);
}


// ============================================================
//  写真・チラシをドライブに置く
// ============================================================

function openFolder_(folderId) {
  try {
    return DriveApp.getFolderById(folderId);
  } catch (error) {
    throw new Error('写真の共有フォルダを開けませんでした。フォルダの編集権限があるか確認してください。');
  }
}

/** base64 で受け取ったファイルをフォルダに置き、閲覧用リンクを返す */
function uploadFile_(folder, file, allowedTypes, baseName, created) {
  if (!file || !file.data) throw new Error('ファイルが空でした。');
  var type = String(file.type || '').toLowerCase();
  if (allowedTypes.indexOf(type) < 0) {
    throw new Error('このファイルの種類は使えません（' + (type || '不明') + '）。');
  }
  var bytes = Utilities.base64Decode(String(file.data));
  if (bytes.length > MAX_FILE_BYTES) {
    throw new Error('ファイルが大きすぎます（20MBまで）。');
  }
  var ext = { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp', 'application/pdf': 'pdf' }[type];
  var blob = Utilities.newBlob(bytes, type, baseName + '.' + ext);
  var saved = folder.createFile(blob);
  created.push(saved);
  try {
    // 自動反映（GitHub Actions）はログインせずに取りに行くので、リンク共有が必要
    saved.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  } catch (error) {
    throw new Error(
      '写真を「リンクを知っている全員が閲覧可」にできませんでした。' +
      'Google Workspace の管理者設定で外部共有が止められている可能性があります。');
  }
  return 'https://drive.google.com/file/d/' + saved.getId() + '/view';
}

function trashAll_(files) {
  files.forEach(function (f) {
    try { f.setTrashed(true); } catch (ignore) { /* 片付けの失敗は無視 */ }
  });
}


// ============================================================
//  小さな道具（tests/ からも呼べるよう、Google の機能は使わない）
// ============================================================

function clean_(value) {
  return String(value == null ? '' : value)
    .replace(/[\r\n\t]+/g, ' ')
    .replace(/　/g, ' ')
    .trim();
}

/** 本文などは改行を残す（生成側で空白に直される） */
function cleanMultiline_(value) {
  return String(value == null ? '' : value)
    .replace(/\r\n?/g, '\n')
    .replace(/　/g, ' ')
    .trim();
}

function isTrue_(value) {
  return TRUE_WORDS.indexOf(String(value == null ? '' : value).trim().toLowerCase()) >= 0;
}

/** 2026/12/1・2026-12-01・2026年12月1日 → 2026-12-01。読めなければ空 */
function normalizeDate_(value) {
  var text = clean_(value).replace(/年|月/g, '-').replace(/日/g, '').replace(/[\/.]/g, '-').replace(/^-+|-+$/g, '');
  var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(text);
  if (!m) return '';
  var y = Number(m[1]), mo = Number(m[2]), d = Number(m[3]);
  var probe = new Date(y, mo - 1, d);
  if (probe.getFullYear() !== y || probe.getMonth() !== mo - 1 || probe.getDate() !== d) return '';
  return y + '-' + ('0' + mo).slice(-2) + '-' + ('0' + d).slice(-2);
}

function orderNumber_(value) {
  var text = String(value == null ? '' : value).replace(/[０-９．]/g, function (ch) {
    return ch === '．' ? '.' : String.fromCharCode(ch.charCodeAt(0) - 0xFEE0);
  }).trim();
  if (!text) return Infinity;
  var n = Number(text);
  return isFinite(n) ? n : Infinity;
}

/** 新しい事例の表示順：先頭なら（いちばん小さい数 − 1）、最後なら（いちばん大きい数 ＋ 1） */
function nextOrder_(orders, position) {
  var nums = orders.map(orderNumber_).filter(function (n) { return isFinite(n); });
  if (nums.length === 0) return 1;
  if (position === 'last') return Math.floor(Math.max.apply(null, nums)) + 1;
  return Math.ceil(Math.min.apply(null, nums)) - 1;
}

function shortName_(text) {
  return clean_(text).replace(/[\\\/:*?"<>|#%]/g, '').slice(0, 20) || '無題';
}

function defaultFlyerText_(type) {
  return type === 'application/pdf' ? 'チラシを開く（PDF）' : 'チラシを開く';
}

function todayString_() {
  return Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd');
}

function safeUserEmail_() {
  try { return Session.getActiveUser().getEmail(); } catch (e) { return ''; }
}


// ============================================================
//  設定の確認（Apps Script の画面で「実行」して使う）
// ============================================================

/** 設定と権限がそろっているかを、実行ログに書き出す */
function 設定を確認する() {
  var config = readConfig_();
  var news = openLedger_(config.newsSheetId, config.newsSheetName, NEWS_REQUIRED, 'お知らせ台帳');
  Logger.log('お知らせ台帳：OK（シート「%s」、%s 行）', news.sheet.getName(), news.sheet.getLastRow() - 1);
  if (config.casesSheetId) {
    var cases = openLedger_(config.casesSheetId, config.casesSheetName, CASE_REQUIRED, '施工事例台帳');
    Logger.log('施工事例台帳：OK（シート「%s」、%s 行）', cases.sheet.getName(), cases.sheet.getLastRow() - 1);
  } else {
    Logger.log('施工事例台帳：未設定（お知らせだけ使えます）');
  }
  var folder = openFolder_(config.photoFolderId);
  Logger.log('写真の共有フォルダ：OK（%s）', folder.getName());
}
