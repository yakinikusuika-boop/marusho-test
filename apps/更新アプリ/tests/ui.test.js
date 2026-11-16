// スマホ画面（index.html）を本物のブラウザで動かして確かめるテスト。
//   使い方:  node apps/更新アプリ/tests/ui.test.js [スクリーンショットの保存先フォルダ]
// google.script.run は偽物に差し替えます（Google にはつながりません）。
'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium, devices } = require('playwright');

const ROOT = path.join(__dirname, '..');
const SITE = path.join(ROOT, '..', '..');
const shotDir = process.argv[2];

const MOCK = `
window.__calls = [];
window.google = { script: { get run() {
  let ok, ng;
  const r = new Proxy({}, { get(_, name) {
    if (name === 'withSuccessHandler') return f => { ok = f; return r; };
    if (name === 'withFailureHandler') return f => { ng = f; return r; };
    return (...args) => {
      window.__calls.push({ name, args });
      setTimeout(() => {
        if (name === 'getInitialData') ok({ user: 'jimu@example.co.jp', siteUrl: 'https://marusho-iwaki.co.jp/',
          news: { categories: ['お知らせ', 'キャンペーン', 'イベント'], recent: [
            { row: 2, date: '2026-11-09', category: 'キャンペーン', title: '年末セールを開催中です', until: '2026-12-31', publish: true },
            { row: 3, date: '2026-07-27', category: 'お知らせ', title: '地元にプロのリフォーム店をオープンしました', publish: false }] },
          cases: { types: ['外壁塗装', '屋根・雨漏り', '水回り', '内装・建具', '外構・その他'], buildings: ['戸建て'],
            recent: [{ row: 2, order: '1', title: '橋の拡張・補修工事', type: '外構・その他', consent: true, publish: true }] } });
        else if (name === 'saveCase' && window.__failNext) { window.__failNext = false; ng(new Error('写真の共有フォルダを開けませんでした。')); }
        else ok({ row: 2, message: '保存しました。10分ほどでサイトに出ます。' });
      }, 30);
    };
  } });
  return r;
} } };`;

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ ...devices['iPhone 13'] });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(MOCK);
  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.waitForSelector('#tab-news:not([hidden])');

  // 横にはみ出さない
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 0, '横スクロールが出ている: ' + overflow);

  // 見出しなしで保存 → 止まる
  await page.click('#saveBtn');
  assert.match(await page.textContent('#message'), /見出しを入れてください/);

  // 写真を選ぶ → 縮小されてプレビュー
  const photo = path.join(SITE, 'lp_image_assets_png/cases/web/kitchen_before.jpg');
  await page.fill('#newsForm [name=title]', '冬季休業のお知らせ');
  await page.fill('#newsForm [name=body]', '12月29日〜1月4日はお休みします。');
  await page.setInputFiles('[data-pick="photo"] input', photo);
  await page.waitForSelector('[data-pick="photo"].has-file img');
  if (shotDir) await page.screenshot({ path: path.join(shotDir, 'app_news.png'), fullPage: true });
  await page.click('#saveBtn');
  await page.waitForFunction(() => document.querySelector('#message .ok'));
  const saved = await page.evaluate(() => window.__calls.find(c => c.name === 'saveNews').args[0]);
  assert.strictEqual(saved.title, '冬季休業のお知らせ');
  assert.strictEqual(saved.publish, true);
  assert.strictEqual(saved.photo.type, 'image/jpeg');
  assert.ok(saved.photo.data.length > 1000);
  assert.match(saved.date, /^\d{4}-\d{2}-\d{2}$/);
  // 保存後はフォームが空に戻る
  assert.strictEqual(await page.inputValue('#newsForm [name=title]'), '');
  assert.strictEqual(await page.locator('[data-pick="photo"].has-file').count(), 0);

  // 施工事例：承諾なしで公開 → 止まる
  await page.click('nav [data-tab=cases]');
  await page.setInputFiles('[data-pick="before"] input', path.join(SITE, 'lp_image_assets_png/cases/web/floor_before.jpg'));
  await page.setInputFiles('[data-pick="after"] input', path.join(SITE, 'lp_image_assets_png/cases/web/floor_after.jpg'));
  await page.waitForSelector('[data-pick="after"].has-file img');
  await page.fill('#caseForm [name=category]', 'フローリング張り替え');
  await page.selectOption('#caseTypes', '内装・建具');
  await page.check('#caseForm [name=publish][value=yes]');
  await page.click('#saveBtn');
  assert.match(await page.textContent('#message'), /承諾/);
  await page.check('#caseForm [name=consent]');
  if (shotDir) await page.screenshot({ path: path.join(shotDir, 'app_cases.png'), fullPage: true });

  // サーバー側のエラーは画面に出て、入力は残る
  await page.evaluate(() => { window.__failNext = true; });
  await page.click('#saveBtn');
  await page.waitForFunction(() => document.querySelector('#message .err'));
  assert.match(await page.textContent('#message'), /共有フォルダ/);
  assert.strictEqual(await page.inputValue('#caseForm [name=category]'), 'フローリング張り替え');
  await page.click('#saveBtn');
  await page.waitForFunction(() => document.querySelector('#message .ok'));
  const c = await page.evaluate(() => window.__calls.filter(c => c.name === 'saveCase').pop().args[0]);
  assert.strictEqual(c.type, '内装・建具');
  assert.strictEqual(c.consent, true);
  assert.strictEqual(c.position, 'first');

  // 登録済み：公開の切り替え
  await page.click('nav [data-tab=list]');
  await page.click('.toggle[data-row="3"][data-kind="news"]');
  await page.waitForFunction(() => window.__calls.some(c => c.name === 'setPublish'));
  const t = await page.evaluate(() => window.__calls.find(c => c.name === 'setPublish').args);
  assert.deepStrictEqual(t, ['news', 3, '地元にプロのリフォーム店をオープンしました', true]);
  if (shotDir) await page.screenshot({ path: path.join(shotDir, 'app_list.png'), fullPage: true });

  assert.deepStrictEqual(errors, []);
  await browser.close();
  console.log('ok  - スマホ画面：入力チェック・写真の縮小・保存・エラー表示・公開切り替え');
})().catch(e => { console.error('NG  - ' + e.stack); process.exit(1); });
