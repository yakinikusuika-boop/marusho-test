# -*- coding: utf-8 -*-
"""
お知らせ台帳の「写真」「リンク」「リンク2」に貼られた Googleドライブのリンクを、
サイトの中のファイルに取り込むスクリプト。

  事務ご担当者様は、共有フォルダに写真やチラシを置いて、
  その「リンクをコピー」を台帳に貼るだけでよくなる。

  使い方:
      python tools/お知らせ写真_取り込み.py \
          --csv "https://docs.google.com/.../gviz/tq?tqx=out:csv&sheet=台帳" \
          --out-csv work/台帳_取り込み済み.csv

  やっていること
    1. 台帳のCSVを読む。
    2. 「写真／リンク／リンク2」の値が Googleドライブのリンクだったら、
       そのファイルを取ってきて lp_image_assets_png/news/ に置く。
         ・写真 ………… 800×500（16:10）のJPEGに作り直す。
                        PDFなら1ページ目を画で起こしてから作り直す。
         ・リンク ……… PDFはそのまま。画像は長辺1600pxまでに収めて保存。
    3. 台帳の値を、置いたファイルのサイト内パスに書き換えたCSVを書き出す。
       → あとは今までどおり tools/お知らせ台帳_生成.py が news.js を作る。

  安全のための決めごと（ここが肝心）
    ・1行の写真が取れなくても、止まらない。その欄だけ空にして先へ進む。
      写真が空の行は、サイト側が標準の写真で出すので、お知らせ自体は必ず出る。
    ・取れなかったことは終了コード 2 で知らせる（ワークフローが赤くなる）。
    ・一度取り込んだファイルは、同じ名前で置いてあるので二度は取りに行かない。
      （10分おきの自動実行で、毎回ダウンロードが走ることはない）
    ・CSVそのものが読めないときだけ終了コード 1。あとの工程は動かさない。

  必要なもの: Pillow, pypdfium2（ワークフローが pip install します）
"""

import argparse
import csv
import hashlib
import io
import os
import re
import sys
import urllib.error
import urllib.request

# ---- 取り込む対象の列 ----
COL_IMAGE = "写真"
COL_LINKS = ["リンク", "リンク2"]

# ---- サイト側の見出し画像の規格（style.css の .news-card-photo に合わせる） ----
THUMB_WIDTH = 800
THUMB_HEIGHT = 500
THUMB_QUALITY = 82

# ---- リンク先として置く画像の上限（長辺） ----
LINK_IMAGE_MAX_EDGE = 1600
LINK_IMAGE_QUALITY = 85

# ---- 受け取る上限（これより大きいファイルは断る） ----
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

warnings = []


def warn(message):
    warnings.append(message)
    sys.stderr.write("【注意】" + message + "\n")


def info(message):
    sys.stderr.write("      " + message + "\n")


def die(message):
    sys.stderr.write("【中止】" + message + "\n")
    sys.stderr.write("        news.js は作り直していません。前の内容のまま公開が続きます。\n")
    sys.exit(1)


# ============================================================
#  Googleドライブのリンクから ファイルID を取り出す
# ============================================================

DRIVE_HOSTS = (
    "drive.google.com",
    "drive.usercontent.google.com",
    "docs.google.com",
    "lh3.googleusercontent.com",
)

_ID = r"([A-Za-z0-9_-]{25,64})"
DRIVE_PATTERNS = [
    re.compile(r"/file/d/" + _ID, re.I),      # .../file/d/<ID>/view
    re.compile(r"/d/" + _ID, re.I),           # .../d/<ID>
    re.compile(r"[?&]id=" + _ID, re.I),        # ...open?id=<ID>
]


def drive_file_id(value):
    """Googleドライブのリンクなら ファイルID を返す。それ以外は None。"""
    if not value:
        return None
    text = value.strip()
    if not re.match(r"^https?://", text, re.I):
        return None
    host = re.sub(r"^https?://", "", text, flags=re.I).split("/")[0].split(":")[0].lower()
    if host not in DRIVE_HOSTS:
        return None
    # スプレッドシート自身のリンクは対象外（取り違えを防ぐ）
    if "/spreadsheets/" in text:
        return None
    for pattern in DRIVE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def short_key(file_id):
    """ファイルIDから、置き場所の名前に使う短い印をつくる。"""
    return hashlib.sha1(file_id.encode("utf-8")).hexdigest()[:10]


# ============================================================
#  取ってくる
# ============================================================

MAGIC = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"%PDF", "pdf"),
]


def sniff_kind(raw):
    """中身の先頭を見て、種類を見分ける。分からなければ None。"""
    for signature, kind in MAGIC:
        if raw.startswith(signature):
            return kind
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(raw) > MAX_DOWNLOAD_BYTES:
        raise ValueError(
            "ファイルが大きすぎます（%d MB まで）" % (MAX_DOWNLOAD_BYTES // (1024 * 1024))
        )
    return raw


def download_drive_file(file_id):
    """公開（リンクを知っている全員が閲覧）されたドライブのファイルを取ってくる。

    返り値: (中身のバイト列, 種類) / 取れなければ (None, 理由の文字列)
    """
    candidates = [
        "https://drive.usercontent.google.com/download?id=%s&export=download" % file_id,
        "https://drive.google.com/uc?export=download&id=%s" % file_id,
        "https://lh3.googleusercontent.com/d/%s=s2048" % file_id,
    ]
    last_reason = "原因が分かりませんでした"

    for url in candidates:
        try:
            raw = fetch(url)
        except urllib.error.HTTPError as error:
            last_reason = "HTTP %s" % error.code
            continue
        except Exception as error:
            last_reason = str(error)
            continue

        kind = sniff_kind(raw)
        if kind:
            return raw, kind

        # 「ウイルスチェックができませんでした」の確認画面が返ることがある
        token = re.search(rb'name="confirm"\s+value="([^"]+)"', raw)
        if token:
            retry = url + "&confirm=" + token.group(1).decode("ascii", "ignore")
            try:
                raw = fetch(retry)
                kind = sniff_kind(raw)
                if kind:
                    return raw, kind
            except Exception as error:
                last_reason = str(error)
                continue

        if b"<html" in raw[:2048].lower() or b"<!doctype" in raw[:2048].lower():
            last_reason = "共有されていない可能性があります（ログイン画面が返りました）"
        else:
            last_reason = "画像でもPDFでもないファイルでした"

    return None, last_reason


# ============================================================
#  画にする
# ============================================================


def open_image(raw, kind):
    """バイト列を Pillow の画像にする。PDFは1ページ目を画で起こす。"""
    from PIL import Image

    if kind == "pdf":
        import pypdfium2

        document = pypdfium2.PdfDocument(io.BytesIO(raw))
        if len(document) == 0:
            raise ValueError("PDFに1ページもありませんでした")
        page = document[0]
        width_pt = page.get_size()[0] or 595.0
        # 横幅が THUMB_WIDTH の2倍くらいになる倍率で起こす（文字がつぶれないように）
        scale = max(1.0, min(4.0, (THUMB_WIDTH * 2.0) / width_pt))
        image = page.render(scale=scale).to_pil().convert("RGB")
        document.close()
        return image, True  # True = 文書なので切り抜いてはいけない

    image = Image.open(io.BytesIO(raw))
    image.load()
    if image.mode not in ("RGB", "L"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode in ("RGBA", "LA", "P"):
            converted = image.convert("RGBA")
            background.paste(converted, mask=converted.split()[-1])
            image = background
        else:
            image = image.convert("RGB")
    else:
        image = image.convert("RGB")
    return image, False


def make_thumbnail(image, is_document, width=THUMB_WIDTH, height=THUMB_HEIGHT):
    """見出し画像をつくる（既定は 800×500。施工事例の取り込みが 800×600 で共用する）。

    ・横長の写真        → 中央で切り抜いて、枠いっぱいに敷く
    ・縦長の写真／文書  → 全体が入るように収め、後ろに自分をぼかして敷く
                          （白い帯が出ないので、チラシでも見栄えが落ちない）
    """
    from PIL import Image, ImageFilter

    source_ratio = image.width / float(image.height)
    crop_allowed = (not is_document) and source_ratio >= 1.0

    if crop_allowed:
        target_ratio = width / float(height)
        if source_ratio > target_ratio:
            new_width = int(round(image.height * target_ratio))
            left = (image.width - new_width) // 2
            box = (left, 0, left + new_width, image.height)
        else:
            new_height = int(round(image.width / target_ratio))
            top = (image.height - new_height) // 2
            box = (0, top, image.width, top + new_height)
        return image.resize(
            (width, height), Image.LANCZOS, box=box
        )

    # 後ろ：枠いっぱいに敷いてから、強くぼかす
    scale = max(width / float(image.width), height / float(image.height))
    backdrop = image.resize(
        (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
        Image.LANCZOS,
    )
    left = (backdrop.width - width) // 2
    top = (backdrop.height - height) // 2
    backdrop = backdrop.crop((left, top, left + width, top + height))
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=24))
    overlay = Image.new("RGB", (width, height), (255, 255, 255))
    backdrop = Image.blend(backdrop, overlay, 0.25)

    # 前：全体が入るように収める
    fit = min(width / float(image.width), height / float(image.height))
    front = image.resize(
        (max(1, int(image.width * fit)), max(1, int(image.height * fit))), Image.LANCZOS
    )
    backdrop.paste(
        front,
        ((width - front.width) // 2, (height - front.height) // 2),
    )
    return backdrop


def save_jpeg(image, path, quality):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    image.save(path, "JPEG", quality=quality, optimize=True, progressive=True)


# ============================================================
#  1つの欄を取り込む
# ============================================================


def find_existing(assets_dir, stem):
    """すでに取り込んであれば、そのパスを返す（二度取りに行かないため）。"""
    if not os.path.isdir(assets_dir):
        return None
    prefix = stem + "."
    for name in sorted(os.listdir(assets_dir)):
        if name.startswith(prefix):
            return os.path.join(assets_dir, name).replace(os.sep, "/")
    return None


def import_photo(file_id, assets_dir, row_number):
    """「写真」の欄。800×500 の見出し画像にして置く。"""
    stem = "news-%s_thumb" % short_key(file_id)
    existing = find_existing(assets_dir, stem)
    if existing:
        return existing

    raw, kind = download_drive_file(file_id)
    if raw is None:
        warn(
            "%d行目：写真を取り込めませんでした（%s）。"
            "この行は標準の写真で出します。お知らせ自体は出ます。" % (row_number, kind)
        )
        return ""

    try:
        image, is_document = open_image(raw, kind)
        thumbnail = make_thumbnail(image, is_document)
    except Exception as error:
        warn(
            "%d行目：写真を画にできませんでした（%s）。"
            "この行は標準の写真で出します。" % (row_number, error)
        )
        return ""

    path = os.path.join(assets_dir, stem + ".jpg").replace(os.sep, "/")
    save_jpeg(thumbnail, path, THUMB_QUALITY)
    info(
        "%d行目：写真を取り込みました → %s（%d KB）"
        % (row_number, path, os.path.getsize(path) // 1024)
    )
    return path


def import_link_file(file_id, assets_dir, row_number, column_name):
    """「リンク」の欄。PDFはそのまま、画像は長辺1600pxまでに収めて置く。"""
    stem = "news-%s" % short_key(file_id)
    existing = find_existing(assets_dir, stem)
    if existing:
        return existing

    raw, kind = download_drive_file(file_id)
    if raw is None:
        warn(
            "%d行目：%sのファイルを取り込めませんでした（%s）。"
            "このリンクは出しません。お知らせ自体は出ます。" % (row_number, column_name, kind)
        )
        return ""

    os.makedirs(assets_dir, exist_ok=True)

    if kind == "pdf":
        path = os.path.join(assets_dir, stem + ".pdf").replace(os.sep, "/")
        with open(path, "wb") as handle:
            handle.write(raw)
        info(
            "%d行目：%sのPDFを取り込みました → %s（%d KB）"
            % (row_number, column_name, path, len(raw) // 1024)
        )
        return path

    try:
        from PIL import Image

        image, _ = open_image(raw, kind)
        longest = max(image.width, image.height)
        if longest > LINK_IMAGE_MAX_EDGE:
            scale = LINK_IMAGE_MAX_EDGE / float(longest)
            image = image.resize(
                (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
                Image.LANCZOS,
            )
    except Exception as error:
        warn(
            "%d行目：%sのファイルを画にできませんでした（%s）。このリンクは出しません。"
            % (row_number, column_name, error)
        )
        return ""

    path = os.path.join(assets_dir, stem + ".jpg").replace(os.sep, "/")
    save_jpeg(image, path, LINK_IMAGE_QUALITY)
    info(
        "%d行目：%sの画像を取り込みました → %s（%d KB）"
        % (row_number, column_name, path, os.path.getsize(path) // 1024)
    )
    return path


# ============================================================
#  台帳を読んで、書き換えたCSVを書き出す
# ============================================================


def load_csv_text(source):
    if re.match(r"^https?://", source, re.I):
        try:
            request = urllib.request.Request(source, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except Exception as error:
            die("台帳の取得に失敗しました（%s）。公開URLの設定を確認してください。" % error)
    else:
        if not os.path.exists(source):
            die("台帳のファイルが見つかりません: %s" % source)
        with open(source, "rb") as handle:
            raw = handle.read()

    if not raw.strip():
        die("台帳が空でした。")

    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    die("台帳の文字コードを判別できませんでした。")


def main():
    parser = argparse.ArgumentParser(
        description="お知らせ台帳のドライブのリンクを、サイトの中のファイルに取り込みます。"
    )
    parser.add_argument("--csv", required=True, help="台帳のCSV（ファイルパス、または公開URL）")
    parser.add_argument("--out-csv", required=True, help="書き換えたCSVの書き出し先")
    parser.add_argument(
        "--assets-dir",
        default="lp_image_assets_png/news",
        help="取り込んだファイルの置き場所（既定: lp_image_assets_png/news）",
    )
    args = parser.parse_args()

    csv_text = load_csv_text(args.csv)
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        die("台帳の1行目（見出しの行）が読めませんでした。")

    headers = [(name or "").replace("﻿", "").strip() for name in reader.fieldnames]
    reader.fieldnames = headers

    rows = list(reader)
    imported = 0

    for offset, row in enumerate(rows):
        row_number = offset + 2  # 1行目は見出し

        if COL_IMAGE in headers:
            value = (row.get(COL_IMAGE) or "").strip()
            file_id = drive_file_id(value)
            if file_id:
                row[COL_IMAGE] = import_photo(file_id, args.assets_dir, row_number)
                imported += 1

        for column_name in COL_LINKS:
            if column_name not in headers:
                continue
            value = (row.get(column_name) or "").strip()
            file_id = drive_file_id(value)
            if file_id:
                row[column_name] = import_link_file(
                    file_id, args.assets_dir, row_number, column_name
                )
                imported += 1

    out_directory = os.path.dirname(args.out_csv)
    if out_directory:
        os.makedirs(out_directory, exist_ok=True)
    with open(args.out_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: (row.get(name) or "") for name in headers})

    sys.stderr.write(
        "ドライブのリンク %d件を見ました。%s を書き出しました。\n" % (imported, args.out_csv)
    )

    if warnings:
        sys.stderr.write("\n注意が %d件ありました（上を確認してください）。\n" % len(warnings))
        sys.exit(2)


if __name__ == "__main__":
    main()
