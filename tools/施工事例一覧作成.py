# -*- coding: utf-8 -*-
"""施工事例一覧ページ（/works/）のカードを作り直すスクリプト
==================================================

■ これは何をするもの？

`cases.js` に書かれている施工事例を読みとって、
`works/index.html` の中のカード部分と絞り込みボタンを書き出します。

トップページの施工事例は、ブラウザが `cases.js` を読んで
その場で組み立てています（HTMLには書かれていません）。
いっぽう `/works/` は **検索結果に出したいページ** なので、
カードをHTMLとして書き出しておきます。検索エンジンが
JavaScript を動かさなくても中身を読めるようにするためです。

■ いつ実行するのですか？

**`cases.js` を書き換えたとき**（事例を足した・減らした・文章を直した・
`type` の分類を変えた）です。

  トップページ … 実行しなくても自動で新しくなります
  /works/      … このスクリプトを実行しないと古いままです

■ 実行のしかた

  1. このファイルがある tools フォルダで、コマンドプロンプトを開く
  2. 次を実行する

       python 施工事例一覧作成.py

  3. 「できました」と出たら、works/index.html が新しくなっています
  4. 写真を新しく足した場合は、その写真の .webp も
     lp_image_assets_png/cases/web/ に置いてください
     （無くても表示されますが、通信量が増えます）

■ 注意

  works/index.html の中の
      <!-- CASES:START -->  〜  <!-- CASES:END -->
      <!-- FILTER:START --> 〜  <!-- FILTER:END -->
  の間は、このスクリプトが毎回まるごと書き換えます。
  **この2組の目印を消さないでください。**
  デザインを直したいときは、この目印の外か style.css を直してください。
"""
import io, os, re, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
CASES_JS = os.path.join(SITE, "cases.js")
PAGE = os.path.join(SITE, "works", "index.html")

# 絞り込みボタンの並び順。cases.js の type がこのどれかに一致します。
# 事例が1件も無い種別のボタンは出しません（押しても0件になるボタンは出さない）。
TYPE_ORDER = ["外壁塗装", "屋根・雨漏り", "水回り", "内装・建具", "外構・その他"]
TYPE_FALLBACK = "外構・その他"


# ============================================================
# 1. cases.js を読む
# ============================================================
def load_cases():
    s = io.open(CASES_JS, encoding="utf-8").read()
    i = s.index("const CASE_ITEMS")
    body = s[s.index("[", i): s.rindex("]") + 1]
    body = re.sub(r"//[^\n]*", "", body)              # 行コメントを外す
    body = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', body)   # 鍵をJSON形式に
    body = re.sub(r",(\s*[}\]])", r"\1", body)        # 末尾のカンマを外す
    try:
        return json.loads(body)
    except Exception as e:
        raise SystemExit("cases.js を読めませんでした：%s\n"
                         "　カンマやダブルクォートの書き忘れがないか確かめてください。" % e)


# ============================================================
# 2. カードのHTMLを組み立てる
# ============================================================
def esc(v):
    return (str("" if v is None else v)
            .replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def img_size(src, default=(800, 600)):
    """写真の実物の大きさを読む（読めなければ 800×600 とみなす）。
       width / height を正しく書いておくと、読み込み前から場所が確保され、
       写真が出た瞬間に文字がずれるのを防げる。"""
    try:
        from PIL import Image
    except ImportError:
        return default
    try:
        with Image.open(os.path.join(SITE, str(src).lstrip("/"))) as im:
            return im.size
    except Exception:
        return default


def photo(src, alt):
    """WebPがあればWebPで、無ければJPEGで出す。
       cases.js に書くのは今までどおり .jpg のパスだけでよい。"""
    jpg = "/" + esc(src).lstrip("/")
    webp = re.sub(r"\.(jpe?g|png)$", ".webp", jpg, flags=re.I)
    w, h = img_size(src)
    return ('<picture><source srcset="%s" type="image/webp">'
            '<img src="%s" alt="%s" loading="lazy" decoding="async" width="%d" height="%d"></picture>'
            % (webp, jpg, esc(alt), w, h))


def card_html(c):
    sp = c.get("spec") or {}
    dt = c.get("detail") or {}
    t = c.get("type") or TYPE_FALLBACK
    if t not in TYPE_ORDER:
        t = TYPE_FALLBACK
    cat = esc(c.get("category"))
    L = "/lp_ui_assets_png/decorations/label_before_green.png"
    R = "/lp_ui_assets_png/decorations/label_after_green.png"

    rows_spec = [("施工箇所", sp.get("location")), ("工期", sp.get("period")),
                 ("費用目安", sp.get("cost")), ("建物種別", sp.get("building"))]
    rows_detail = [("工事前の悩み", dt.get("problem")), ("施工内容", dt.get("work")),
                   ("施工後の変化", dt.get("change")), ("担当者コメント", dt.get("comment"))]
    # 空の項目は行ごと出さない（分からない内容を作らないため）
    spec = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (k, esc(v))
                   for k, v in rows_spec if str(v or "").strip())
    detail = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (k, esc(v))
                     for k, v in rows_detail if str(v or "").strip())

    link = str(c.get("link") or "").strip()
    btn = ('\n          <a href="%s" class="btn btn-orange">%s の事例を詳しく見る <span class="arw">→</span></a>'
           % (esc(link), cat)) if link else ""

    return """      <article class="case-card" data-type="%s">
        <div class="case-ba">
          <figure>%s<img src="%s" alt="Before" class="ba-label ba-label--l" loading="lazy" width="160" height="54"></figure>
          <figure>%s<img src="%s" alt="After" class="ba-label ba-label--r" loading="lazy" width="160" height="54"></figure>
        </div>
        <div class="case-body">
          <span class="case-tag">%s</span>
          <dl class="case-spec">%s</dl>
          <dl class="case-detail">%s</dl>%s
        </div>
      </article>""" % (
        esc(t),
        photo(c.get("before"), cat + " 施工前"), L,
        photo(c.get("after"), cat + " 施工後"), R,
        cat, spec, detail, btn)


def filter_html(items):
    counts = {}
    for c in items:
        t = c.get("type") or TYPE_FALLBACK
        if t not in TYPE_ORDER:
            t = TYPE_FALLBACK
        counts[t] = counts.get(t, 0) + 1
    btns = ['      <button type="button" class="works-filter-btn is-on" data-type="all" aria-pressed="true">'
            'すべて<span class="n">%d</span></button>' % len(items)]
    for t in TYPE_ORDER:
        if counts.get(t):
            btns.append('      <button type="button" class="works-filter-btn" data-type="%s" aria-pressed="false">'
                        '%s<span class="n">%d</span></button>' % (esc(t), esc(t), counts[t]))
    return ('    <div class="works-filter" id="worksFilter" role="group" aria-label="工事種別で絞り込む">\n'
            + "\n".join(btns) + "\n    </div>")


# ============================================================
# 3. works/index.html に差し込む
# ============================================================
def replace_block(s, name, new):
    a, b = "<!-- %s:START -->" % name, "<!-- %s:END -->" % name
    if a not in s or b not in s:
        raise SystemExit("works/index.html に %s の目印がありません。消してしまった可能性があります。" % name)
    head = s[:s.index(a) + len(a)]
    tail = s[s.index(b):]
    return head + "\n" + new + "\n    " + tail


def main():
    items = [c for c in load_cases() if c.get("category")]
    if not items:
        raise SystemExit("cases.js に事例が1件もありません。")
    s = io.open(PAGE, encoding="utf-8", newline="").read()
    s = replace_block(s, "CASES", "\n".join(card_html(c) for c in items))
    s = replace_block(s, "FILTER", filter_html(items))
    io.open(PAGE, "w", encoding="utf-8", newline="").write(s)

    print("できました。事例 %d 件を works/index.html に書き出しました。" % len(items))
    print("このあと、style.css や index.html の ?v=… の日付を新しくしてから GitHub に上げてください。")


if __name__ == "__main__":
    main()
