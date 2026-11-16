// Code.gs を、偽の台帳・偽のドライブの上で動かして確かめるテスト。
//   使い方:  node apps/更新アプリ/tests/server.test.js
// Google の本物には一切つながりません。
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

// ---- 偽の台帳 ----
function makeSheet(name, rows, checkboxCols) {
  // rows: 2次元配列（1行目が見出し）。checkboxCols: チェックボックスの列番号（1始まり）
  const cells = rows.map(r => r.slice());
  const width = () => Math.max(0, ...cells.map(r => r.length));
  const validation = {};               // "r,c" -> 'CHECKBOX'
  for (let r = 2; r <= cells.length; r++) (checkboxCols || []).forEach(c => { validation[r + ',' + c] = 'CHECKBOX'; });
  const display = v => v === true ? 'TRUE' : v === false ? 'FALSE' : v == null ? '' : String(v);
  const get = (r, c) => (cells[r - 1] || [])[c - 1];
  const sheet = {
    getName: () => name,
    getLastRow: () => {
      for (let r = cells.length; r >= 1; r--) if (cells[r - 1].some(v => v !== '' && v != null)) return r;
      return 0;
    },
    getLastColumn: width,
    insertRowBefore(row) {
      cells.splice(row - 1, 0, new Array(width()).fill(''));
      const moved = {};
      Object.keys(validation).forEach(k => {
        const [r, c] = k.split(',').map(Number);
        moved[(r >= row ? r + 1 : r) + ',' + c] = validation[k];
      });
      Object.keys(validation).forEach(k => delete validation[k]);
      Object.assign(validation, moved);
    },
    getRange(r, c, nr = 1, nc = 1) {
      return {
        r, c, nr, nc,
        getDisplayValues: () => Array.from({ length: nr }, (_, i) => Array.from({ length: nc }, (_, j) => display(get(r + i, c + j)))),
        getDisplayValue: () => display(get(r, c)),
        setValue(v) {
          while (cells.length < r) cells.push(new Array(width()).fill(''));
          while (cells[r - 1].length < c) cells[r - 1].push('');
          cells[r - 1][c - 1] = v;
        },
        getDataValidation: () => validation[r + ',' + c]
          ? { getCriteriaType: () => 'CHECKBOX' } : null,
        copyTo(to, type) {
          if (type !== 'DATA_VALIDATION') return;
          for (let j = 0; j < nc; j++) {
            const v = validation[r + ',' + (c + j)];
            if (v) validation[to.r + ',' + (c + j)] = v;
          }
        }
      };
    },
    _cells: cells,
    _validation: validation
  };
  return sheet;
}

function loadApp({ newsSheet, casesSheet, props, failSharing }) {
  const files = [];
  const context = {
    console,
    SpreadsheetApp: {
      openById: id => {
        if (id === 'NEWS') return { getSheets: () => [newsSheet], getSheetByName: n => n === newsSheet.getName() ? newsSheet : null };
        if (id === 'CASES') return { getSheets: () => [casesSheet], getSheetByName: n => n === casesSheet.getName() ? casesSheet : null };
        throw new Error('no such sheet');
      },
      flush() {},
      CopyPasteType: { PASTE_FORMAT: 'FORMAT', PASTE_DATA_VALIDATION: 'DATA_VALIDATION' },
      DataValidationCriteria: { CHECKBOX: 'CHECKBOX' }
    },
    PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] || '' }) },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    DriveApp: {
      Access: { ANYONE_WITH_LINK: 'ANYONE_WITH_LINK' },
      Permission: { VIEW: 'VIEW' },
      getFolderById: () => ({
        getName: () => '写真',
        createFile(blob) {
          const f = { id: 'FILE' + String(files.length + 1).padStart(30, '0'), blob, trashed: false, sharing: null };
          files.push(f);
          return {
            getId: () => f.id,
            setSharing(a, p) { if (failSharing) throw new Error('policy'); f.sharing = a + '/' + p; },
            setTrashed(t) { f.trashed = t; }
          };
        }
      })
    },
    Utilities: {
      base64Decode: s => Array.from(Buffer.from(s, 'base64')),
      newBlob: (bytes, type, name) => ({ bytes, type, name }),
      formatDate: () => '2026-11-16'
    },
    Session: { getActiveUser: () => ({ getEmail: () => 'staff@example.com' }) },
    HtmlService: {},
    Logger: { log() {} }
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Code.gs'), 'utf8'), context);
  return { app: context, files };
}

const NEWS_HEAD = ['掲載日', '種別', '見出し', '本文', '掲載終了日', '公開', '写真', 'リンク', 'リンク文字', 'リンク2', 'リンク2文字', '過去へ下げる'];
const CASE_HEAD = ['表示順', '種別', '分類', '施工箇所', '工期', '費用目安', '建物種別', '工事前の悩み', '施工内容', '施工後の変化', '担当者コメント', 'ビフォー写真', 'アフター写真', 'リンク', '施主承諾', '公開'];
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64').toString('base64');
const props = { NEWS_SHEET_ID: 'NEWS', CASES_SHEET_ID: 'CASES', PHOTO_FOLDER_ID: 'FOLDER' };

function fresh(opts = {}) {
  const newsSheet = makeSheet('台帳', [
    NEWS_HEAD,
    ['2026-11-09', 'キャンペーン', '年末セールを開催中です', '本文', '2026-12-31', true, '', '', '', '', '', false],
    ['2026-07-27', 'お知らせ', 'オープンしました', '', '', true, '', '', '', '', '', false]
  ], [6, 12]);
  const casesSheet = makeSheet('施工事例', [
    CASE_HEAD,
    [1, '橋の拡張・補修工事', '外構・その他', '', '', '', '', '', '', '', '', 'a.jpg', 'b.jpg', '', true, true],
    [2, '外壁塗装（クリーム色）', '外壁塗装', '', '', '', '戸建て', '', '', '', '', 'c.jpg', 'd.jpg', '', true, true],
    ['', '', '', '', '', '', '', '', '', '', '', '', '', '', false, false]
  ], [15, 16]);
  return { newsSheet, casesSheet, ...loadApp({ newsSheet, casesSheet, props: opts.props || props, failSharing: opts.failSharing }) };
}

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log('ok  - ' + name); }
  catch (e) { console.log('NG  - ' + name + '\n      ' + e.stack); process.exitCode = 1; }
}
const col = (head, name) => head.indexOf(name);

// ---------------------------------------------------------------
test('お知らせは2行目に入り、既存の行は下にずれる', () => {
  const { app, newsSheet, files } = fresh();
  const res = app.saveNews({ date: '2026-11-16', until: '2026-11-30', category: 'お知らせ', title: '冬季休業のお知らせ',
    body: '12/29〜1/4は休みます\n2行目', publish: true, photo: { name: 'a.jpg', type: 'image/jpeg', data: PNG } });
  assert.strictEqual(res.row, 2);
  const row = newsSheet._cells[1];
  assert.strictEqual(row[col(NEWS_HEAD, '見出し')], '冬季休業のお知らせ');
  assert.strictEqual(row[col(NEWS_HEAD, '掲載日')], '2026-11-16');
  assert.strictEqual(row[col(NEWS_HEAD, '公開')], true, 'チェックボックス列には true を入れる');
  assert.match(row[col(NEWS_HEAD, '写真')], /^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]{25,}\/view$/);
  assert.strictEqual(newsSheet._cells[2][col(NEWS_HEAD, '見出し')], '年末セールを開催中です');
  assert.strictEqual(files[0].sharing, 'ANYONE_WITH_LINK/VIEW');
  assert.strictEqual(newsSheet._validation['2,6'], 'CHECKBOX', '差し込んだ行にもチェックボックスが付く');
});

test('写真のリンクは、取り込みスクリプトの読み取り規則（/file/d/<ID>）に合う', () => {
  const { app, newsSheet } = fresh();
  app.saveNews({ date: '2026-11-16', title: 't', publish: true, photo: { name: 'a', type: 'image/jpeg', data: PNG } });
  const url = newsSheet._cells[1][col(NEWS_HEAD, '写真')];
  // tools/お知らせ写真_取り込み.py の DRIVE_PATTERNS と同じ
  assert.match(url, /\/file\/d\/([A-Za-z0-9_-]{25,64})/);
});

test('チラシ（PDF）はリンク列へ、ボタン文字が空なら既定の文字', () => {
  const { app, newsSheet, files } = fresh();
  app.saveNews({ date: '2026-11-16', title: 'チラシ', publish: true,
    flyer: { name: 'x.pdf', type: 'application/pdf', data: Buffer.from('%PDF-1.4').toString('base64') } });
  const row = newsSheet._cells[1];
  assert.match(row[col(NEWS_HEAD, 'リンク')], /drive\.google\.com\/file\/d\//);
  assert.strictEqual(row[col(NEWS_HEAD, 'リンク文字')], 'チラシを開く（PDF）');
  assert.match(files[0].blob.name, /\.pdf$/);
});

test('下書きは 公開=false', () => {
  const { app, newsSheet } = fresh();
  const res = app.saveNews({ date: '2026/11/16', title: '下書き', publish: false });
  assert.strictEqual(newsSheet._cells[1][col(NEWS_HEAD, '公開')], false);
  assert.match(res.message, /下書き/);
});

test('見出し・日付の不備は台帳を触らずに止める', () => {
  const { app, newsSheet } = fresh();
  const before = JSON.stringify(newsSheet._cells);
  assert.throws(() => app.saveNews({ date: '2026-11-16', title: ' ' }), /見出し/);
  assert.throws(() => app.saveNews({ date: '2026-02-30', title: 'x' }), /掲載日/);
  assert.throws(() => app.saveNews({ date: '2026-11-16', until: '2026-11-01', title: 'x' }), /掲載終了日/);
  assert.strictEqual(JSON.stringify(newsSheet._cells), before);
});

test('数式に見える入力は文字として入れる', () => {
  const { app, newsSheet } = fresh();
  app.saveNews({ date: '2026-11-16', title: '=IMPORTXML("x")', publish: false });
  assert.strictEqual(newsSheet._cells[1][col(NEWS_HEAD, '見出し')], "'=IMPORTXML(\"x\")");
});

test('共有できなかったら、置いた写真を片付けて止める', () => {
  const { app, newsSheet, files } = fresh({ failSharing: true });
  const before = JSON.stringify(newsSheet._cells);
  assert.throws(() => app.saveNews({ date: '2026-11-16', title: 'x', photo: { name: 'a', type: 'image/jpeg', data: PNG } }), /リンクを知っている全員/);
  assert.strictEqual(files[0].trashed, true);
  assert.strictEqual(JSON.stringify(newsSheet._cells), before);
});

test('使えない種類のファイルは断る', () => {
  const { app } = fresh();
  assert.throws(() => app.saveNews({ date: '2026-11-16', title: 'x', photo: { name: 'a.heic', type: 'image/heic', data: PNG } }), /種類/);
});

test('施工事例は空いている行に入り、先頭なら表示順は最小−1', () => {
  const { app, casesSheet } = fresh();
  const res = app.saveCase({ category: '洗面台交換', type: '水回り', building: '戸建て', consent: true, publish: true, position: 'first',
    before: { name: 'b', type: 'image/jpeg', data: PNG }, after: { name: 'a', type: 'image/jpeg', data: PNG } });
  assert.strictEqual(res.row, 4, '空のチェックボックスだけの行を使う');
  const row = casesSheet._cells[3];
  assert.strictEqual(row[col(CASE_HEAD, '表示順')], 0);
  assert.strictEqual(row[col(CASE_HEAD, '種別')], '洗面台交換');
  assert.strictEqual(row[col(CASE_HEAD, '施主承諾')], true);
  assert.match(row[col(CASE_HEAD, 'ビフォー写真')], /drive\.google\.com/);
  assert.match(row[col(CASE_HEAD, 'アフター写真')], /drive\.google\.com/);
});

test('施工事例：最後なら表示順は最大＋1、空き行が無ければ下に足す', () => {
  const { app, casesSheet } = fresh();
  const pic = { name: 'b', type: 'image/jpeg', data: PNG };
  app.saveCase({ category: 'A', type: '水回り', consent: false, publish: false, position: 'last', before: pic, after: pic });
  const res = app.saveCase({ category: 'B', type: '水回り', consent: false, publish: false, position: 'last', before: pic, after: pic });
  assert.strictEqual(casesSheet._cells[3][0], 3);
  assert.strictEqual(res.row, 5);
  assert.strictEqual(casesSheet._cells[4][0], 4);
});

test('施工事例：承諾なしの公開は断る', () => {
  const { app } = fresh();
  const pic = { name: 'b', type: 'image/jpeg', data: PNG };
  assert.throws(() => app.saveCase({ category: 'A', type: '水回り', consent: false, publish: true, before: pic, after: pic }), /承諾/);
  assert.throws(() => app.saveCase({ category: 'A', type: '謎', consent: true, publish: true, before: pic, after: pic }), /分類/);
});

test('公開の切り替え：見出しが一致したときだけ書き換える', () => {
  const { app, newsSheet } = fresh();
  app.setPublish('news', 2, '年末セールを開催中です', false);
  assert.strictEqual(newsSheet._cells[1][col(NEWS_HEAD, '公開')], false);
  assert.throws(() => app.setPublish('news', 2, '別の見出し', true), /行が動いていた/);
  assert.strictEqual(newsSheet._cells[1][col(NEWS_HEAD, '公開')], false);
});

test('施工事例の公開切り替えは承諾が必要', () => {
  const { app, casesSheet } = fresh();
  casesSheet._cells[1][col(CASE_HEAD, '施主承諾')] = false;
  assert.throws(() => app.setPublish('cases', 2, '橋の拡張・補修工事', true), /承諾/);
});

test('画面用データ：最近の一覧と候補', () => {
  const { app } = fresh();
  const data = app.getInitialData();
  assert.strictEqual(data.news.recent.length, 2);
  assert.strictEqual(data.news.recent[0].publish, true);
  assert.ok(data.news.categories.includes('キャンペーン'));
  assert.deepStrictEqual(Array.from(data.cases.recent.map(c => c.title)), ['橋の拡張・補修工事', '外壁塗装（クリーム色）']);
});

test('施工事例台帳が未設定でも、お知らせは使える', () => {
  const { app } = fresh({ props: { NEWS_SHEET_ID: 'NEWS', PHOTO_FOLDER_ID: 'FOLDER' } });
  assert.strictEqual(app.getInitialData().cases, null);
  assert.throws(() => app.saveCase({}), /CASES_SHEET_ID/);
});

test('列が足りない台帳は使わない', () => {
  const newsSheet = makeSheet('台帳', [['掲載日', '見出し']], []);
  const { app } = loadApp({ newsSheet, casesSheet: newsSheet, props });
  assert.throws(() => app.getInitialData(), /見出しの行が見つかりません/);
});

console.log('\n' + passed + ' 件 通過');
