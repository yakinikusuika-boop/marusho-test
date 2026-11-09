# -*- coding: utf-8 -*-
"""
お知らせ台帳（Googleスプレッドシート／CSV）から news.js を作り直すスクリプト。

  使い方（ローカルのCSVから）:
      python tools/お知らせ台帳_生成.py --csv 台帳.csv --out news.js
  使い方（公開URLから直接）:
      python tools/お知らせ台帳_生成.py --csv "https://docs.google.com/.../pub?output=csv" --out news.js

  安全のための決めごと（ここが肝心）
    1. 取得に失敗した／必要な列が無い／公開対象が0件 のときは news.js を書き換えない。
       → 台帳をうっかり壊しても、サイトのお知らせが真っ白になることはない。
    2. 行ごとの軽い不備（見出しが空、日付の形がおかしい）は、その行だけ飛ばして続行し、
       終了コード 2 を返す。ワークフロー側は「公開はするが、担当者へ通知する」扱いにする。
    3. 致命的な不備は終了コード 1。news.js はそのまま。

  標準ライブラリだけで動くので、GitHub Actions 側に pip install は不要。
"""

import argparse
import csv
import io
import os
import re
import sys
import urllib.request

# ---- 台帳の列名（スプレッドシートの1行目と完全に一致させる） ----
COL_DATE = "掲載日"
COL_CATEGORY = "種別"
COL_TITLE = "見出し"
COL_BODY = "本文"
COL_UNTIL = "掲載終了日"
COL_PUBLISH = "公開"
COL_IMAGE = "写真"
COL_LINK1 = "リンク"
COL_LABEL1 = "リンク文字"
COL_LINK2 = "リンク2"
COL_LABEL2 = "リンク2文字"
COL_ARCHIVE = "過去へ下げる"

REQUIRED_COLUMNS = [COL_DATE, COL_CATEGORY, COL_TITLE, COL_PUBLISH]

TRUE_WORDS = set(
    ["true", "1", "yes", "y", "はい", "○", "◯", "〇", "✓", "✔", "レ", "x", "ｘ", "×"]
)

warnings = []


def warn(message):
    warnings.append(message)
    sys.stderr.write("【注意】" + message + "\n")


def die(message):
    sys.stderr.write("【中止】" + message + "\n")
    sys.stderr.write("        news.js は書き換えていません。前の内容のまま公開が続きます。\n")
    sys.exit(1)


def load_csv_text(source):
    """ファイルパスでも http(s) URL でも読み込む。"""
    if re.match(r"^https?://", source, re.I):
        try:
            request = urllib.request.Request(
                source, headers={"User-Agent": "marusho-news-builder"}
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


def cell(row, name):
    """セルを取り出して、前後の空白・改行・全角空白を整える。"""
    value = row.get(name) or ""
    value = value.replace("\r", " ").replace("\n", " ")
    return value.replace("　", " ").strip()


def is_true(value):
    return value.strip().lower() in TRUE_WORDS


def normalize_date(value, row_number, column_name):
    """2026/12/1 や 2026.12.1、2026年12月1日 を 2026-12-01 に直す。"""
    if not value:
        return ""
    text = value.replace("年", "-").replace("月", "-").replace("日", "")
    text = text.replace("/", "-").replace(".", "-").strip().strip("-")
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if not match:
        warn(
            "%d行目：%sの書き方「%s」が分かりませんでした。この欄は無視します。"
            % (row_number, column_name, value)
        )
        return ""
    year, month, day = (int(part) for part in match.groups())
    if not (1 <= month <= 12 and 1 <= day <= 31):
        warn(
            "%d行目：%s「%s」は存在しない日付です。この欄は無視します。"
            % (row_number, column_name, value)
        )
        return ""
    return "%04d-%02d-%02d" % (year, month, day)


def js_string(value):
    """JavaScript の文字列リテラルとして安全な形に直す。"""
    out = value.replace("\\", "\\\\").replace('"', '\\"')
    return out.replace(" ", " ").replace(" ", " ")


def read_items(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        die("台帳の1行目（見出しの行）が読めませんでした。")

    headers = [(name or "").replace("﻿", "").strip() for name in reader.fieldnames]
    missing = [name for name in REQUIRED_COLUMNS if name not in headers]
    if missing:
        die("台帳に必要な列がありません: %s（1行目の見出しを直してください）" % "／".join(missing))

    reader.fieldnames = headers

    items = []
    for offset, row in enumerate(reader):
        row_number = offset + 2  # 1行目は見出し

        if not any((value or "").strip() for value in row.values() if value is not None):
            continue  # 空行は黙って飛ばす

        if not is_true(cell(row, COL_PUBLISH)):
            continue  # 「公開」に印が無い行は下書き扱い

        title = cell(row, COL_TITLE)
        if not title:
            warn("%d行目：見出しが空のため、この行は掲載しません。" % row_number)
            continue

        item = {
            "date": normalize_date(cell(row, COL_DATE), row_number, COL_DATE),
            "until": normalize_date(cell(row, COL_UNTIL), row_number, COL_UNTIL),
            "category": cell(row, COL_CATEGORY) or "お知らせ",
            "title": title,
            "body": cell(row, COL_BODY),
            "image": cell(row, COL_IMAGE),
            "archive": is_true(cell(row, COL_ARCHIVE)),
            "row": row_number,
        }

        link1, label1 = cell(row, COL_LINK1), cell(row, COL_LABEL1)
        link2, label2 = cell(row, COL_LINK2), cell(row, COL_LABEL2)

        if link1 and link2:
            # リンクが2本あるときは links（行ごとのリンク）として出す
            item["links"] = [
                {"url": link1, "label": label1 or link1},
                {"url": link2, "label": label2 or link2},
            ]
        else:
            if link2 and not link1:
                warn("%d行目：リンク2だけが入っています。リンクの欄から先に埋めてください。" % row_number)
                link1, label1 = link2, label2
            if label1 and not link1:
                warn("%d行目：リンク文字だけが入っています（リンク先が空）。文字だけが出ます。" % row_number)
            item["link"] = link1
            item["linkText"] = label1

        items.append(item)

    if not items:
        die("公開する行が1件もありませんでした。「公開」の欄に印が入っているか確認してください。")

    return items


def build_js(items, ledger_url):
    lines = []
    lines.append("/* ============================================================")
    lines.append("   お知らせ・イベント情報のデータ")
    lines.append("")
    lines.append("   ■ このファイルは自動で作られています。直接編集しないでください。")
    lines.append("     次回の自動反映のときに、ここでの手直しは消えてしまいます。")
    lines.append("")
    lines.append("   ■ 内容を直すところ：お知らせ台帳（スプレッドシート）")
    if ledger_url:
        lines.append("     " + ledger_url)
    lines.append("")
    lines.append("   ■ 作り直しているもの：tools/お知らせ台帳_生成.py")
    lines.append("     （.github/workflows/news-from-sheet.yml が定期的に実行します）")
    lines.append("   ============================================================ */")
    lines.append("")
    lines.append("const NEWS_ITEMS = [")

    for index, item in enumerate(items):
        lines.append("  // ---- %d件目（台帳 %d行目） ----" % (index + 1, item["row"]))
        lines.append("  {")

        field_lines = []
        field_lines.append('    date: "%s",' % js_string(item["date"]))
        if item["until"]:
            field_lines.append(
                '    until: "%s",   // 掲載終了日。翌日から過去のお知らせへ'
                % js_string(item["until"])
            )
        if item["archive"]:
            field_lines.append("    archive: true,")
        field_lines.append('    category: "%s",' % js_string(item["category"]))
        field_lines.append('    title: "%s",' % js_string(item["title"]))
        if item["body"]:
            field_lines.append('    body: "%s",' % js_string(item["body"]))
        if item["image"]:
            field_lines.append('    image: "%s",' % js_string(item["image"]))

        if "links" in item:
            field_lines.append("    links: [")
            for link_index, link in enumerate(item["links"]):
                comma = "," if link_index < len(item["links"]) - 1 else ""
                field_lines.append('      { url: "%s",' % js_string(link["url"]))
                field_lines.append(
                    '        label: "%s" }%s' % (js_string(link["label"]), comma)
                )
            field_lines.append("    ],")
        else:
            if item["link"]:
                field_lines.append('    link: "%s",' % js_string(item["link"]))
            if item["linkText"]:
                field_lines.append('    linkText: "%s",' % js_string(item["linkText"]))

        # 最後の行の末尾のカンマだけ外す
        field_lines[-1] = re.sub(r",$", "", field_lines[-1])
        lines.extend(field_lines)
        lines.append("  }," if index < len(items) - 1 else "  }")

    lines.append("];")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="お知らせ台帳から news.js を作り直します。")
    parser.add_argument("--csv", required=True, help="台帳のCSV（ファイルパス、または公開URL）")
    parser.add_argument("--out", default="news.js", help="書き出し先（既定: news.js）")
    parser.add_argument("--ledger-url", default="", help="台帳のURL（生成ファイルの案内に書きます）")
    parser.add_argument("--dry-run", action="store_true", help="書き出さずに結果だけ見る")
    args = parser.parse_args()

    csv_text = load_csv_text(args.csv)
    items = read_items(csv_text)
    javascript = build_js(items, args.ledger_url.strip())

    if args.dry_run:
        sys.stdout.write(javascript)
    else:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(javascript)
        sys.stderr.write("掲載 %d件を %s に書き出しました。\n" % (len(items), args.out))

    if warnings:
        sys.stderr.write("\n注意が %d件ありました（上を確認してください）。\n" % len(warnings))
        sys.exit(2)


if __name__ == "__main__":
    main()
