# -*- coding: utf-8 -*-
"""
本番サイトから「練習用サイト」を作り直すスクリプト。

  使い方:
      cd 00_サイト本体/公開用_marusho-site
      python tools/練習用サイト_作成.py

  できるもの:
      00_サイト本体/練習用_marusho-renshu/      ← これを marusho-renshu リポジトリへ push する
      公開先: https://yakinikusuika-boop.github.io/marusho-renshu/

  なぜスクリプトにするか
      練習用サイトを手で作ると、本番を直したときに置いていかれて
      「練習したとおりにならない」状態になる。本番を直したらこれを
      もう一度走らせるだけで、練習用も最新になる。

  本番から変えているところ（安全のため）
      1. お問い合わせフォームを止める   … 練習の送信が本社に届かないようにする
      2. アクセス解析を外す             … GA4・Clarity に練習の記録が混ざらないようにする
      3. noindex と robots.txt          … 検索結果に練習用が出ないようにする
      4. canonical・OGP・構造化データを外す … 本番と取り違えられないようにする
      5. CNAME と sitemap.xml を入れない … 本番ドメインを奪わないようにする
      6. 赤い帯を全ページに出す         … 本番と見間違えないようにする
      7. タイトルに【練習用】を付ける     … ブラウザのタブで見分けられるようにする
      8. ルート始まりのパスに /marusho-renshu/ を足す … GitHub Pages の階層に合わせる
"""

import argparse
import os
import re
import shutil
import sys
import time

# この階層（tools/）の1つ上が本番サイト
SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DST = os.path.join(os.path.dirname(SITE_DIR), "練習用_marusho-renshu")
DEFAULT_BASE = "/marusho-renshu/"

# 練習用には持っていかないもの
SKIP_NAMES = {
    ".git",            # 練習用リポジトリ自身の履歴は消さない（後述の clean で守る）
    ".claude",
    "CNAME",           # 本番ドメインの主張。練習用に置くと衝突する
    "sitemap.xml",     # 検索エンジンへの地図。練習用には不要
    "analytics.js",    # 読み込む側は消してあるが、ファイルごと置かない（戻されないように）
}
SKIP_DIRS = {
    os.path.join("tools", "_元ファイル"),  # フォント元ファイル（30MB×5）
}
SKIP_SUFFIXES = (".bak", ".orig", "~", ".pyc")

BANNER_ID = "renshu-banner"
BANNER_TEXT = "練習用サイト ― 本番ではありません。ここで何をしても、お客様が見るホームページは変わりません。"
BANNER_TEXT_SHORT = "練習用サイト ― 本番ではありません"
BANNER_HEIGHT = 34

BANNER_STYLE = """
<!-- ===== 練習用サイトの目印（tools/練習用サイト_作成.py が入れています） ===== -->
<style>
  body { padding-top: %(h)dpx !important; }
  .site-header { top: %(h)dpx !important; }
  #%(id)s {
    position: fixed; top: 0; left: 0; right: 0; height: %(h)dpx; z-index: 500;
    background: #B3261E; color: #fff; text-align: center;
    font: bold 13px/%(h)dpx "Meiryo", sans-serif;
    letter-spacing: .02em; overflow: hidden; white-space: nowrap;
  }
  #%(id)s .renshu-short { display: none; }
  @media (max-width: 720px) {
    #%(id)s { font-size: 11px; }
    #%(id)s .renshu-long { display: none; }
    #%(id)s .renshu-short { display: inline; }
  }
</style>
""" % {"h": BANNER_HEIGHT, "id": BANNER_ID}

BANNER_HTML = """
<div id="%(id)s">
  <span class="renshu-long">%(long)s</span>
  <span class="renshu-short">%(short)s</span>
</div>
<script>
  /* 練習用サイト：お問い合わせが本番に飛ばないよう、送信そのものを止めています。
     捕捉フェーズで止めるので、ページ側の送信処理は動きません。 */
  document.addEventListener('submit', function (e) {
    e.preventDefault();
    e.stopImmediatePropagation();
    alert('ここは練習用サイトです。お問い合わせは送信されません。');
  }, true);
</script>
""" % {"id": BANNER_ID, "long": BANNER_TEXT, "short": BANNER_TEXT_SHORT}

ROBOTS_TXT = """# 練習用サイト（株式会社丸翔）
# 本番は https://marusho-iwaki.co.jp/ です。
#
# ここは事務ご担当者様が練習するための場所なので、
# 検索エンジンには一切載せません。各ページにも noindex を入れています。

User-agent: *
Disallow: /
"""

README_MD = """# 練習用サイト（marusho-renshu）

**このフォルダは手で編集しないでください。**
`公開用_marusho-site/tools/練習用サイト_作成.py` が作り直しています。

- 本番：https://marusho-iwaki.co.jp/
- 練習用：https://yakinikusuika-boop.github.io/marusho-renshu/

## 本番を直したら

```
cd 00_サイト本体/公開用_marusho-site
python tools/練習用サイト_作成.py
```

これで練習用も最新の見た目になります。そのうえで練習用リポジトリへ push してください。

## 本番から変えているところ

1. お問い合わせフォームは送信できません（練習の送信が本社に届かないように）
2. アクセス解析（GA4・Clarity）を外しています
3. `noindex` と `robots.txt` で検索結果に出ないようにしています
4. `canonical`・OGP・構造化データを外しています
5. `CNAME`・`sitemap.xml` を置いていません
6. 全ページの上に赤い帯が出ます
7. タイトルの先頭に【練習用】が付きます

## お知らせの練習について

練習用サイトのお知らせは、**練習用のお知らせ台帳**から作られます。
本番の台帳とは別のスプレッドシートです。取り違えないでください。
"""

report = []


def note(message):
    report.append(message)


def remove_with_retry(path, tries=12, wait=0.4):
    """Dropbox が同期中にファイルを掴んでいることがあるので、少し待って何度か試す。"""
    for attempt in range(tries):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return True
        except PermissionError:
            if attempt == tries - 1:
                return False
            time.sleep(wait)
    return False


def remove_stale(dst, keep, generated):
    """本番に無くなったファイルを、練習用からも消す。

    フォルダごと消す（rmtree）のはやめている。ここは Dropbox の中なので、
    同期中はフォルダを掴まれて rmdir が失敗する。ファイル単位なら待って再試行できる。
    """
    removed = 0
    locked = []
    for root, dirs, files in os.walk(dst):
        dirs[:] = [d for d in dirs if d != ".git"]
        for filename in files:
            path = os.path.join(root, filename)
            rel = os.path.relpath(path, dst)
            if rel in keep or rel in generated:
                continue
            if remove_with_retry(path):
                removed += 1
            else:
                locked.append(rel)

    # 空になったフォルダは消せたら消す（消せなくても害は無い）
    for root, dirs, files in os.walk(dst, topdown=False):
        if os.path.basename(root) == ".git" or os.sep + ".git" + os.sep in root + os.sep:
            continue
        if root == dst:
            continue
        try:
            if not os.listdir(root):
                os.rmdir(root)
        except OSError:
            pass

    return removed, locked


def should_skip(rel_path):
    name = os.path.basename(rel_path)
    if name in SKIP_NAMES:
        return True
    if name.endswith(SKIP_SUFFIXES):
        return True
    if re.search(r"\.\d{8}bak", name):
        return True
    for skip_dir in SKIP_DIRS:
        if rel_path == skip_dir or rel_path.startswith(skip_dir + os.sep):
            return True
    return False


def copy_tree(src, dst):
    """本番から練習用へ上書きコピーし、持っていった相対パスの一覧を返す。"""
    copied = set()
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        if rel_root == ".":
            rel_root = ""
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(rel_root, d))]
        for filename in files:
            rel_path = os.path.join(rel_root, filename) if rel_root else filename
            if should_skip(rel_path):
                continue
            target = os.path.join(dst, rel_path)
            parent = os.path.dirname(target)
            if parent:
                os.makedirs(parent, exist_ok=True)
            shutil.copy2(os.path.join(root, filename), target)
            copied.add(rel_path)
    return copied


def strip_blocks(html, filename):
    """アクセス解析・canonical・OGP・構造化データを外す。"""
    counts = {}

    def drop(pattern, label, flags=0):
        nonlocal html
        html, n = re.subn(pattern, "", html, flags=flags)
        if n:
            counts[label] = counts.get(label, 0) + n

    # アクセス解析（GA4 の読み込み・gtag の設定・Clarity・自前の analytics.js）
    drop(r"[ \t]*<!-- =+ アクセス解析[^\n]*-->\n?", "解析のコメント")
    drop(r"[ \t]*<!-- =+ ヒートマップ[^\n]*-->\n?", "解析のコメント")
    drop(r"[ \t]*<script async src=\"https://www\.googletagmanager\.com[^\"]*\"></script>\n?", "GA4の読み込み")
    drop(r"[ \t]*<script>\s*\n\s*window\.dataLayer.*?</script>\n?", "gtagの設定", re.S)
    drop(r"[ \t]*<script type=\"text/javascript\">(?:(?!</script>).)*?clarity.*?</script>\n?", "Clarity", re.S)
    # 404.html と works/index.html は src="/analytics.js" とルート始まりで書いているので
    # 先頭の「/」を省略可にしておく（ここを取りこぼすと解析タグが練習用に残る）
    drop(r"[ \t]*<script src=\"/?analytics\.js[^\"]*\"[^>]*></script>\n?", "analytics.js")

    # 検索エンジン向けの指定
    drop(r"[ \t]*<!-- =+ 正規URL（canonical）[^>]*?-->\n?", "canonicalのコメント", re.S)
    drop(r"[ \t]*<link rel=\"canonical\"[^>]*>\n?", "canonical")
    drop(r"[ \t]*<!-- =+ OGP・Twitterカード(?:(?!-->).)*?-->\n?", "OGPのコメント", re.S)
    drop(r"[ \t]*<meta property=\"og:[^>]*>\n?", "OGP")
    drop(r"[ \t]*<meta name=\"twitter:[^>]*>\n?", "Twitterカード")
    drop(r"[ \t]*<!-- =+ 構造化データ(?:(?!-->).)*?-->\n?", "構造化データのコメント", re.S)
    drop(r"[ \t]*<script type=\"application/ld\+json\">.*?</script>\n?", "構造化データ", re.S)

    if counts:
        note("  %s から外したもの: %s" % (filename, "、".join(
            "%s×%d" % (k, v) for k, v in counts.items())))
    return html


def transform_html(html, filename, base):
    html = strip_blocks(html, filename)

    # noindex を入れる。
    #   すでに <meta name="robots"> がある紙（coupon.html・404.html）は中身を書き換え、
    #   無い紙は viewport の直後に足す。
    #   ※ 置換後の文字列に r"..." を使って \" と書くと、バックスラッシュがそのまま
    #     書き込まれてしまう。ここは素のシングルクォートで書くこと。
    robots_tag = '<meta name="robots" content="noindex,nofollow">'
    if re.search(r'<meta name="robots"[^>]*>', html):
        html = re.sub(r'<meta name="robots"[^>]*>', robots_tag, html)
    else:
        html, n = re.subn(
            r'(<meta name="viewport"[^>]*>)',
            '\\1\n' + robots_tag,
            html, count=1)
        if not n:
            note("  !! %s : viewport が見つからず noindex を入れられませんでした" % filename)

    # タイトルに【練習用】を付ける
    html, n = re.subn(r"<title>(?!【練習用】)", "<title>【練習用】", html, count=1)
    if not n and "<title>" in html:
        note("  !! %s : タイトルに印を付けられませんでした" % filename)

    # ルート始まりのパスを、GitHub Pages の階層に合わせる
    #   href="/works/" → href="/marusho-renshu/works/"
    #   「//」で始まるもの（//example.com）は書き換えない
    prefix = "/" + base.strip("/") + "/"
    html, n_path = re.subn(r"(href|src)=\"/(?!/)", r'\1="%s' % prefix, html)
    if n_path:
        note("  %s : ルート始まりのパスを %d か所 %s に直しました" % (filename, n_path, prefix))

    # お問い合わせフォームの送信先を外す（念のための二重の備え）
    html, n_act = re.subn(r"action=\"https://ssgform\.com/[^\"]*\"", 'action="#"', html)
    html, n_ep = re.subn(
        r"(const FORM_ENDPOINT\s*=\s*)'[^']*'", r"\1''", html)
    if n_act or n_ep:
        note("  %s : フォームの送信先を外しました（action×%d / FORM_ENDPOINT×%d）"
             % (filename, n_act, n_ep))

    # 赤い帯と、送信を止めるしかけを入れる
    html, n_style = re.subn(r"(</head>)", BANNER_STYLE.rstrip() + r"\n\1", html, count=1)
    html, n_banner = re.subn(r"(<body[^>]*>)", r"\1\n" + BANNER_HTML.rstrip(), html, count=1)
    if not (n_style and n_banner):
        note("  !! %s : 赤い帯を入れられませんでした（head=%d body=%d）"
             % (filename, n_style, n_banner))

    return html


def verify(dst, base):
    """できあがった練習用サイトを自分で点検する。

    本番を直して作り直すたびに、ここが通ることを確かめる。
    1つでも落ちたら、練習用を公開してはいけない（本番と取り違えられる／
    練習の問い合わせが本社に届く／検索結果に練習用が出る、のいずれかが起きる）。
    """
    prefix = "/" + base.strip("/") + "/"
    pages = []
    for root, dirs, files in os.walk(dst):
        dirs[:] = [d for d in dirs if d != ".git"]
        for filename in files:
            if filename.endswith(".html"):
                pages.append(os.path.join(root, filename))

    checks = []

    def check(ok, label):
        checks.append((bool(ok), label))

    check(pages, "HTML が1枚以上ある")
    check(not os.path.exists(os.path.join(dst, "CNAME")), "CNAME を置いていない")
    check(not os.path.exists(os.path.join(dst, "sitemap.xml")), "sitemap.xml を置いていない")

    robots_path = os.path.join(dst, "robots.txt")
    robots_ok = os.path.exists(robots_path)
    if robots_ok:
        with open(robots_path, encoding="utf-8") as handle:
            robots_ok = "Disallow: /" in handle.read()
    check(robots_ok, "robots.txt が Disallow: / になっている")

    bad = {
        "解析タグの残り": [],
        "noindex の入れ漏れ": [],
        "赤い帯の入れ漏れ": [],
        "タイトルの印の漏れ": [],
        "フォーム送信先の残り": [],
        "canonical・OGP・構造化データの残り": [],
        "パスの二重化": [],
        "バックスラッシュの紛れ込み": [],
    }

    for path in pages:
        rel = os.path.relpath(path, dst).replace("\\", "/")
        with open(path, encoding="utf-8") as handle:
            html = handle.read()

        if re.search(r"googletagmanager|clarity\.ms|analytics\.js", html):
            bad["解析タグの残り"].append(rel)
        if '<meta name="robots" content="noindex,nofollow">' not in html:
            bad["noindex の入れ漏れ"].append(rel)
        if 'id="%s"' % BANNER_ID not in html:
            bad["赤い帯の入れ漏れ"].append(rel)
        if "<title>" in html and "<title>【練習用】" not in html:
            bad["タイトルの印の漏れ"].append(rel)
        if "ssgform.com" in html:
            bad["フォーム送信先の残り"].append(rel)
        if re.search(r'rel="canonical"|property="og:|application/ld\+json', html):
            bad["canonical・OGP・構造化データの残り"].append(rel)
        if prefix.strip("/") + "/" + prefix.strip("/") in html:
            bad["パスの二重化"].append(rel)
        if re.search(r'name=\\"|content=\\"', html):
            bad["バックスラッシュの紛れ込み"].append(rel)

    for label, files in bad.items():
        check(not files, "%s（%s）" % (label, "／".join(files) if files else "なし"))

    print()
    print("---- 自己点検 ----")
    failed = 0
    for ok, label in checks:
        print(("  OK   " if ok else "  NG   ") + label)
        if not ok:
            failed += 1
    print("------------------")
    if failed:
        print("NG が %d 件あります。直すまで練習用サイトを公開しないでください。" % failed)
    else:
        print("すべて通りました。")
    return failed


def main():
    parser = argparse.ArgumentParser(description="本番サイトから練習用サイトを作り直します。")
    parser.add_argument("--dst", default=DEFAULT_DST, help="書き出し先フォルダ")
    parser.add_argument("--base", default=DEFAULT_BASE,
                        help="GitHub Pages の階層（既定: /marusho-renshu/）")
    args = parser.parse_args()

    src = SITE_DIR
    dst = os.path.abspath(args.dst)

    if os.path.abspath(src) == dst:
        sys.stderr.write("書き出し先が本番と同じです。中止します。\n")
        sys.exit(1)

    print("本番  : %s" % src)
    print("練習用: %s" % dst)
    print("階層  : %s" % ("/" + args.base.strip("/") + "/"))
    print()

    if not os.path.isdir(dst):
        os.makedirs(dst)

    copied = copy_tree(src, dst)
    note("ファイルを %d 個 持っていきました" % len(copied))

    generated = {"robots.txt", "README.md"}
    removed, locked = remove_stale(dst, copied, generated)
    if removed:
        note("本番に無くなったファイルを %d 個 消しました" % removed)
    if locked:
        note("  !! 消せなかったファイル（Dropbox が掴んでいます）: %s"
             % "／".join(locked[:5]))

    # HTML を1枚ずつ作り変える
    html_count = 0
    for root, dirs, files in os.walk(dst):
        dirs[:] = [d for d in dirs if d != ".git"]
        for filename in sorted(files):
            if not filename.endswith(".html"):
                continue
            path = os.path.join(root, filename)
            rel = os.path.relpath(path, dst).replace("\\", "/")
            with open(path, encoding="utf-8") as handle:
                html = handle.read()
            html = transform_html(html, rel, args.base)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(html)
            html_count += 1
    note("HTML を %d 枚 作り変えました" % html_count)

    # 検索エンジン向けと、説明書き
    with open(os.path.join(dst, "robots.txt"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(ROBOTS_TXT)
    with open(os.path.join(dst, "README.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(README_MD)
    note("robots.txt（Disallow: /）と README.md を置きました")

    # ワークフローの名前を変えて、練習用だと分かるようにする
    workflow = os.path.join(dst, ".github", "workflows", "news-from-sheet.yml")
    if os.path.exists(workflow):
        with open(workflow, encoding="utf-8") as handle:
            text = handle.read()
        text = text.replace("name: お知らせ台帳の反映", "name: お知らせ台帳の反映（練習用）")
        with open(workflow, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        note("ワークフローの名前に「（練習用）」を付けました")

    print("\n".join(report))

    failed = verify(dst, args.base)
    if failed:
        sys.exit(1)

    print()
    print("できました。あとは %s を marusho-renshu リポジトリへ push してください。" % dst)


if __name__ == "__main__":
    main()
