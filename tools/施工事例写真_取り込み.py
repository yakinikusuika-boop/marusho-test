# -*- coding: utf-8 -*-
"""
施工事例台帳の「ビフォー写真」「アフター写真」に貼られた Googleドライブのリンクを、
サイトの中のファイルに取り込むスクリプト。

  事務ご担当者様は、共有フォルダに写真を置いて、
  その「リンクをコピー」を台帳に貼るだけでよくなる。

  使い方:
      python tools/施工事例写真_取り込み.py \
          --csv work/cases_raw.csv \
          --out-csv work/cases.csv

  やっていること
    1. 台帳のCSVを読む。
    2. 「ビフォー写真／アフター写真」の値が Googleドライブのリンクだったら、
       そのファイルを取ってきて lp_image_assets_png/cases/web/ に置く。
         ・写真は 400×300（4:3）のJPEGに作り直す。
           縦長の写真は切り抜かず、全体が入るように収めて後ろをぼかす。
         ・/works/ のカードが .webp を参照するので、同じ名前の .webp も必ず作る。
    3. 台帳の値を、置いたファイルのサイト内パスに書き換えたCSVを書き出す。
       → あとは tools/施工事例台帳_生成.py が cases.js を作る。

  安全のための決めごと（ここが肝心）
    ・1枚の写真が取れなくても、止まらない。その欄だけ空にして先へ進む。
      ただし施工事例は写真が無いと出せないので、生成側がその行を飛ばす
      （＝その事例だけ出ない。ほかの事例と、お知らせはそのまま出る）。
    ・PDFは受け付けない（施工写真はビフォー／アフターの写真のみ）。
    ・取れなかったことは終了コード 2 で知らせる（ワークフローが赤くなる）。
    ・一度取り込んだファイルは、同じ名前で置いてあるので二度は取りに行かない。
    ・CSVそのものが読めないときだけ終了コード 1。あとの工程は動かさない。

  必要なもの: Pillow（ワークフローが pip install します）
  ドライブからの取得・縮小の道具は tools/お知らせ写真_取り込み.py のものを共用。
"""

import argparse
import csv
import importlib.util
import io
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 取り込む対象の列 ----
PHOTO_COLUMNS = ["ビフォー写真", "アフター写真"]

# ---- サイト側の施工事例写真の規格（既存の lp_image_assets_png/cases/web/ に合わせる） ----
# 表示は170px幅（スマホ163px）の4:3枠。2026-09-18 に既存写真を400px幅へ縮小ずみ
# （コミット 4856890）。800px で作ると、新しい事例だけ4倍の重さになる。
CASE_WIDTH = 400
CASE_HEIGHT = 300
JPEG_QUALITY = 82
WEBP_QUALITY = 80

USER_AGENT_NOTE = "marusho-cases-builder"

warnings = []


def warn(message):
    warnings.append(message)
    sys.stderr.write("【注意】" + message + "\n")


def info(message):
    sys.stderr.write("      " + message + "\n")


def die(message):
    sys.stderr.write("【中止】" + message + "\n")
    sys.stderr.write("        cases.js は作り直していません。前の内容のまま公開が続きます。\n")
    sys.exit(1)


def load_news_tools():
    """お知らせ写真_取り込み.py を部品として読み込む（取得・縮小の道具を共用）。"""
    path = os.path.join(HERE, "お知らせ写真_取り込み.py")
    if not os.path.exists(path):
        die("tools/お知らせ写真_取り込み.py が見つかりません。")
    spec = importlib.util.spec_from_file_location("news_photo_tools", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


news = load_news_tools()


def load_csv_text(source):
    if re.match(r"^https?://", source, re.I):
        try:
            request = urllib.request.Request(
                source, headers={"User-Agent": USER_AGENT_NOTE}
            )
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


def save_webp(image, path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    image.save(path, "WEBP", quality=WEBP_QUALITY, method=6)


def ensure_webp(jpg_path, webp_path):
    """jpg はあるのに webp が無いとき（途中で止まった跡）、jpg から作り足す。"""
    if os.path.exists(webp_path):
        return
    try:
        from PIL import Image

        with Image.open(jpg_path) as image:
            save_webp(image.convert("RGB"), webp_path)
        info("webp を作り足しました → %s" % webp_path.replace(os.sep, "/"))
    except Exception as error:
        warn("webp を作れませんでした（%s）。JPEGだけで表示されます。" % error)


def import_case_photo(file_id, assets_dir, row_number, column_name):
    """写真の欄。400×300 の JPEG と webp にして置く。"""
    stem = "case-%s" % news.short_key(file_id)
    jpg_path = os.path.join(assets_dir, stem + ".jpg").replace(os.sep, "/")
    webp_path = os.path.join(assets_dir, stem + ".webp").replace(os.sep, "/")

    if os.path.exists(jpg_path):
        ensure_webp(jpg_path, webp_path)
        return jpg_path

    raw, kind = news.download_drive_file(file_id)
    if raw is None:
        warn(
            "%d行目：%sを取り込めませんでした（%s）。"
            "写真がそろうまで、この事例は掲載されません。" % (row_number, column_name, kind)
        )
        return ""

    if kind == "pdf":
        warn(
            "%d行目：%sにPDFが貼られています。施工事例の写真の欄には"
            "写真（JPEG・PNGなど）を貼ってください。この事例は掲載されません。"
            % (row_number, column_name)
        )
        return ""

    try:
        image, _ = news.open_image(raw, kind)
        thumbnail = news.make_thumbnail(image, False, CASE_WIDTH, CASE_HEIGHT)
    except Exception as error:
        warn(
            "%d行目：%sを画にできませんでした（%s）。"
            "写真がそろうまで、この事例は掲載されません。" % (row_number, column_name, error)
        )
        return ""

    news.save_jpeg(thumbnail, jpg_path, JPEG_QUALITY)
    try:
        save_webp(thumbnail, webp_path)
    except Exception as error:
        warn("%d行目：webp を作れませんでした（%s）。JPEGだけで表示されます。" % (row_number, error))
    info(
        "%d行目：%sを取り込みました → %s（%d KB）"
        % (row_number, column_name, jpg_path, os.path.getsize(jpg_path) // 1024)
    )
    return jpg_path


def main():
    parser = argparse.ArgumentParser(
        description="施工事例台帳のドライブのリンクを、サイトの中のファイルに取り込みます。"
    )
    parser.add_argument("--csv", required=True, help="台帳のCSV（ファイルパス、または公開URL）")
    parser.add_argument("--out-csv", required=True, help="書き換えたCSVの書き出し先")
    parser.add_argument(
        "--assets-dir",
        default="lp_image_assets_png/cases/web",
        help="取り込んだ写真の置き場所（既定: lp_image_assets_png/cases/web）",
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

        for column_name in PHOTO_COLUMNS:
            if column_name not in headers:
                continue
            value = (row.get(column_name) or "").strip()
            file_id = news.drive_file_id(value)
            if file_id:
                row[column_name] = import_case_photo(
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
