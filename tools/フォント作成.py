# -*- coding: utf-8 -*-
"""サイトで使うWebフォントを作り直すスクリプト
==================================================

■ これは何をするもの？

このサイトは、文字の書体（Noto Sans JP など）を Google のサーバーから
借りるのをやめて、サイト自身に置いて配信しています。
そのとき「サイトに出てくる文字ぶんだけ」に削ったファイルを使うことで、
通信量を大きく減らしています。

  Google から借りていたとき … ページを最後まで読むと約2,457KB
  いまのやり方            … 全部で約498KB

■ いつ実行するのですか？

**お知らせや施工事例に、今までサイトに無かった漢字を書き足したとき**です。
削ったファイルに入っていない字は、パソコンやスマホにもともと入っている
書体で表示されます（読めなくなるわけではありませんが、そこだけ字の形が
少し変わります）。気になったらこれを実行してください。

文章を直しただけ・写真を入れ替えただけなら、実行は要りません。

■ 実行のしかた

  1. このファイルがある tools フォルダで、コマンドプロンプトを開く
  2. 次を1行ずつ実行する

       python -m pip install "fonttools[woff]"
       python フォント作成.py

  3. 「できました」と出たら、fonts フォルダの中身が新しくなっています
  4. index.html の style.css?v=... の日付を新しくして、GitHubに上げる

  ※ 元の書体ファイル（約30MB）は毎回インターネットから取り直します。
     ネットにつながっている必要があります。

■ 書体のライセンス

Noto Sans JP・Yuji Mai・Yuji Syuku は SIL Open Font License 1.1 です。
削って使うこと、自分のサーバーから配ることが認められています。
条件として、ライセンス文を一緒に置く必要があります（fonts/OFL.txt）。
**この OFL.txt を消さないでください。**
"""
import io, os, re, sys, json, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
FONTS = os.path.join(SITE, "fonts")
CACHE = os.path.join(HERE, "_元ファイル")

# Google Fonts は、相手のブラウザによって返すファイルの種類を変える。
# 古い端末のふりをすると、分割していない1本もののTTFが返ってくる。それを材料にする。
UA_OLD = ("Mozilla/5.0 (Linux; U; Android 4.3; ja-jp; SC-02F Build/JSS15J) "
          "AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30")

SOURCES = [
    ("NotoSansJP-400", "family=Noto+Sans+JP:wght@400"),
    ("NotoSansJP-700", "family=Noto+Sans+JP:wght@700"),
    ("NotoSansJP-900", "family=Noto+Sans+JP:wght@900"),
    ("YujiMai-400",    "family=Yuji+Mai"),
    ("YujiSyuku-400",  "family=Yuji+Syuku"),
]


# ============================================================
# 1. サイトに出てくる文字を集める
# ============================================================
def rng(a, z):
    return set(chr(c) for c in range(a, z + 1))

# 日本語を書くのに要る文字は、サイトに出ていなくても入れておく。
# ひらがな・カタカナ・数字・記号は数が少なく、入れても容量がほとんど増えないため。
# 漢字だけは数が多いので「サイトに出ている字」に限る。
BASE = (
    rng(0x20, 0x7E)                  # 英数字と記号
    | rng(0x3000, 0x303F)            # 、。「」〒〜 など
    | rng(0x3040, 0x309F)            # ひらがな
    | rng(0x30A0, 0x30FF)            # カタカナ
    | rng(0xFF01, 0xFF5E)            # 全角の英数と記号
    | rng(0xFF61, 0xFF9F)            # 半角カタカナ
    | set("※○●◎△▲▽▼□■◇◆☆★♪♭♯→←↑↓⇒⇔─│┌┐└┘├┤┬┴┼")
    | set("±×÷≠≦≧∞√∴♂♀°′″℃℉¥＄％‰§¶†‡№℡㎡㎥㎏㎜㎝㎞㍿㈱㈲")
    | set("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮ⅠⅡⅢⅣⅤ")
    | set("…‥―‐–—“”‘’・／＼｜〔〕【】《》〈〉『』")
    | set("©®™£€¢«»·")
)

TEXT_FILES = ["index.html", "privacy.html", "coupon.html", "404.html",
              "works/index.html",
              "cases.js", "news.js", "analytics.js"]
# ※CSS（style.css）は読んでいません。
#   CSSの content:"…" で画面に文字を出すときは、ここで拾えないため、
#   BASE に入っている記号（英数字・ひらがな・カタカナ・全角記号など）を使ってください。


def site_chars():
    """サイトのファイルから、画面に出る文字を拾い集める。
       取りこぼすと字が欠けるので、多めに拾う（多く拾っても害はない）。"""
    chars = set()
    for name in TEXT_FILES:
        p = os.path.join(SITE, name)
        if not os.path.isfile(p):
            continue
        s = io.open(p, encoding="utf-8").read()
        if name.endswith(".html"):
            # タグを外した本文
            body = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S)
            chars |= set(re.sub(r"<[^>]+>", " ", body))
            # alt や placeholder などタグの中の文言
            chars |= set(" ".join(re.findall(
                r'(?:alt|title|placeholder|content|value|aria-label)="([^"]*)"', s)))
        # JS の中の文言も、画面に出るものがある（事例・お知らせ・フォームの案内）
        chars |= set(s)
    return {c for c in chars if ord(c) >= 0x20 and c != "�"}


def deco_chars():
    """装飾書体（筆文字）を使う場所の文字だけ。ここは増やさない。"""
    s = io.open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    def grab(a, b):
        i = s.index(a)
        return re.sub(r"<[^>]+>", "", s[i:s.index(b, i)])
    sign = "山内 寿徳"
    catch = grab('<h3 class="greeting-catch">', "</h3>")
    return set(sign), set(catch + sign)


# ============================================================
# 2. 元の書体ファイルを取ってくる
# ============================================================
def download():
    os.makedirs(CACHE, exist_ok=True)
    def get(url, ua=UA_OLD):
        return urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": ua})).read()

    for name, q in SOURCES:
        dst = os.path.join(CACHE, name + ".ttf")
        if os.path.isfile(dst) and os.path.getsize(dst) > 1_000_000:
            print("  %-16s すでにあるので使い回します" % name)
            continue
        css = get("https://fonts.googleapis.com/css2?" + q).decode("utf-8")
        urls = re.findall(r"url\((\S+?)\)", css)
        if len(urls) != 1:
            raise SystemExit("想定外：%s で %d 件のURLが返りました" % (name, len(urls)))
        print("  %-16s 取得中…" % name)
        io.open(dst, "wb").write(get(urls[0]))


# ============================================================
# 3. 文字を絞って woff2 にする
# ============================================================
def build():
    try:
        from fontTools.ttLib import TTFont
        from fontTools.subset import Subsetter, Options
    except ImportError:
        raise SystemExit(
            '先に次を実行してください：\n    python -m pip install "fonttools[woff]"')

    os.makedirs(FONTS, exist_ok=True)
    body = site_chars() | BASE
    mai, syuku = deco_chars()

    plan = [
        ("NotoSansJP-400", "noto-sans-jp-400.woff2", body),
        ("NotoSansJP-700", "noto-sans-jp-700.woff2", body),
        ("NotoSansJP-900", "noto-sans-jp-900.woff2", body),
        ("YujiMai-400",    "yuji-mai.woff2",         mai),
        ("YujiSyuku-400",  "yuji-syuku.woff2",       syuku),
    ]

    total = 0
    for src_name, out_name, chars in plan:
        opts = Options()
        opts.flavor = "woff2"
        opts.desubroutinize = False
        opts.layout_features = ["kern", "liga", "clig", "calt", "ccmp",
                                "locl", "palt", "mark", "mkmk"]
        opts.name_IDs = ["*"]        # 著作権とライセンスの表記は必ず残す（OFLの条件）
        opts.name_legacy = True
        opts.notdef_outline = True
        opts.hinting = False

        font = TTFont(os.path.join(CACHE, src_name + ".ttf"))
        sub = Subsetter(options=opts)
        sub.populate(unicodes=[ord(c) for c in chars])
        sub.subset(font)
        font.flavor = "woff2"
        out = os.path.join(FONTS, out_name)
        font.save(out)
        font.close()

        n = os.path.getsize(out)
        total += n
        print("  %-22s %5d文字  %7.1fKB" % (out_name, len(chars), n / 1024))
    return total, body


# ============================================================
# 4. ライセンス文を置く
# ============================================================
def license_file():
    dst = os.path.join(FONTS, "OFL.txt")
    if os.path.isfile(dst):
        print("  OFL.txt はすでにあります")
        return
    url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/OFL.txt"
    txt = urllib.request.urlopen(url).read().decode("utf-8")
    io.open(dst, "w", encoding="utf-8", newline="\n").write(txt)
    print("  OFL.txt を置きました")


if __name__ == "__main__":
    print("【1/3】元の書体ファイルを用意します")
    download()
    print("\n【2/3】サイトに出てくる文字だけに絞ります")
    total, body = build()
    print("\n【3/3】ライセンス文を確認します")
    license_file()
    print("\n=== できました ===")
    print("  fonts フォルダの合計 %.1fKB（%d文字ぶん）" % (total / 1024, len(body)))
    print("  index.html の style.css?v=... の日付を新しくして、GitHubに上げてください。")
