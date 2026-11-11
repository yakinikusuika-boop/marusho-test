# -*- coding: utf-8 -*-
"""
施工事例台帳（Googleスプレッドシート／CSV）から cases.js を作り直すスクリプト。

  使い方（ローカルのCSVから）:
      python tools/施工事例台帳_生成.py --csv 台帳.csv --out cases.js
  使い方（公開URLから直接）:
      python tools/施工事例台帳_生成.py --csv "https://docs.google.com/.../pub?output=csv" --out cases.js

  台帳の列（1行目の見出しと完全に一致させる）
      表示順 …… 数字。小さい順にサイトへ並ぶ（10, 20, 30…と振ると間に挿しやすい）
      種別 ……… 見出しの緑バッジ（例「外壁塗装（ツートン）」）。空の行は掲載しない
      分類 ……… /works/ の絞り込み。「外壁塗装／屋根・雨漏り／水回り／内装・建具／外構・その他」の5択
      施工箇所・工期・費用目安・建物種別 …… 表の4項目（空欄はその行だけ出ない）
      工事前の悩み・施工内容・施工後の変化・担当者コメント …… 説明の4項目（同上）
      ビフォー写真・アフター写真 …… 取り込み後のサイト内パス。両方そろわない行は掲載しない
      リンク ……… 「詳しく見る」ボタンの行き先。空欄ならボタンは出ない
      施主承諾 … ✓が無い行は、公開✓があっても掲載しない（お施主様の承諾が先）
      公開 ……… ✓で掲載。外せば下書き

  安全のための決めごと（お知らせ台帳_生成.py と同じ）
    1. 取得に失敗した／必要な列が無い／掲載できる行が0件 のときは cases.js を書き換えない。
       → 台帳をうっかり壊しても、サイトの施工事例が真っ白になることはない。
    2. 行ごとの軽い不備（写真が片方だけ、承諾✓なし など）は、その行だけ飛ばして続行し、
       終了コード 2 を返す。ワークフロー側は「公開はするが、担当者へ通知する」扱いにする。
    3. 致命的な不備は終了コード 1。cases.js はそのまま。

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
COL_ORDER = "表示順"
COL_CATEGORY = "種別"
COL_TYPE = "分類"
COL_LOCATION = "施工箇所"
COL_PERIOD = "工期"
COL_COST = "費用目安"
COL_BUILDING = "建物種別"
COL_PROBLEM = "工事前の悩み"
COL_WORK = "施工内容"
COL_CHANGE = "施工後の変化"
COL_COMMENT = "担当者コメント"
COL_BEFORE = "ビフォー写真"
COL_AFTER = "アフター写真"
COL_LINK = "リンク"
COL_CONSENT = "施主承諾"
COL_PUBLISH = "公開"

REQUIRED_COLUMNS = [
    COL_ORDER, COL_CATEGORY, COL_TYPE,
    COL_BEFORE, COL_AFTER, COL_CONSENT, COL_PUBLISH,
]

# /works/ の絞り込み分類（tools/施工事例一覧作成.py の TYPE_ORDER と同じ並び）
TYPE_ORDER = ["外壁塗装", "屋根・雨漏り", "水回り", "内装・建具", "外構・その他"]
TYPE_FALLBACK = "外構・その他"

# 表示順が読めない行を回す先（いちばん後ろ）
ORDER_LAST = 10 ** 9

TRUE_WORDS = set(
    ["true", "1", "yes", "y", "はい", "○", "◯", "〇", "✓", "✔", "レ", "x", "ｘ", "×"]
)

warnings = []


def warn(message):
    warnings.append(message)
    sys.stderr.write("【注意】" + message + "\n")


def die(message):
    sys.stderr.write("【中止】" + message + "\n")
    sys.stderr.write("        cases.js は書き換えていません。前の内容のまま公開が続きます。\n")
    sys.exit(1)


def load_csv_text(source):
    """ファイルパスでも http(s) URL でも読み込む。"""
    if re.match(r"^https?://", source, re.I):
        try:
            request = urllib.request.Request(
                source, headers={"User-Agent": "marusho-cases-builder"}
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


def parse_order(value, row_number):
    """表示順の数字を読む。読めなければ、いちばん後ろに回す。"""
    if not value:
        warn("%d行目：表示順が空です。この行はいちばん後ろに回します。" % row_number)
        return ORDER_LAST
    text = value.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        return float(text)
    except ValueError:
        warn(
            "%d行目：表示順「%s」が数字として読めません。この行はいちばん後ろに回します。"
            % (row_number, value)
        )
        return ORDER_LAST


def check_photo(path, row_number, column_name):
    """写真の欄は「サイトの中のファイル」だけを通す。

    ドライブのリンクのまま（＝取り込みに失敗した）だと表示できないので、
    空として扱い、呼び出し側がその行を飛ばす。
    """
    if not path:
        return ""
    if re.match(r"^[\w./-]+\.(jpg|jpeg|png|webp)(\?|$)", path, re.I):
        return path
    warn(
        "%d行目：%s「%s」はサイトの中のファイルではありません（取り込みに失敗した可能性）。"
        % (row_number, column_name, path)
    )
    return ""


def check_link(url, row_number):
    """リンクの書き方をざっと見て、出せないものは出さない。"""
    if not url:
        return ""

    if " " in url:
        warn("%d行目：リンクに空白が入っています。貼り直してください。" % row_number)

    if re.match(r"^http://", url, re.I):
        warn(
            "%d行目：リンクが http:// で始まっています。https:// のリンクを貼り直してください。"
            % row_number
        )
        return url

    if re.match(r"^https://", url, re.I):
        host = re.sub(r"^https://", "", url, flags=re.I).split("/")[0].lower()
        if "drive.google.com" in host or "docs.google.com" in host:
            warn(
                "%d行目：リンクがGoogleドライブのリンクのままです。"
                "施工事例のリンクには、サイトの中のページか https:// のページを貼ってください。"
                "この欄は出しません。" % row_number
            )
            return ""
        return url

    # サイトの中のファイル・ページ（coupon.html など）
    if re.match(r"^[\w./-]+\.(pdf|html|jpg|jpeg|png|webp)(\?|$)", url, re.I):
        return url
    if re.match(r"^[\w./-]+/$", url):  # works/ のようなフォルダ形
        return url

    warn(
        "%d行目：リンク「%s」は、リンクとして使える形ではありません。この欄は出しません。"
        % (row_number, url)
    )
    return ""


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

        if not is_true(cell(row, COL_CONSENT)):
            warn(
                "%d行目：公開✓が入っていますが、施主承諾✓がありません。"
                "お施主様の承諾を確かめてから✓を入れてください。この行は掲載しません。"
                % row_number
            )
            continue

        category = cell(row, COL_CATEGORY)
        if not category:
            warn("%d行目：種別が空のため、この行は掲載しません。" % row_number)
            continue

        before = check_photo(cell(row, COL_BEFORE), row_number, COL_BEFORE)
        after = check_photo(cell(row, COL_AFTER), row_number, COL_AFTER)
        if not (before and after):
            warn(
                "%d行目：ビフォー写真とアフター写真の両方がそろっていないため、"
                "この行は掲載しません。" % row_number
            )
            continue

        case_type = cell(row, COL_TYPE)
        if case_type and case_type not in TYPE_ORDER:
            warn(
                "%d行目：分類「%s」は5つの分類にありません。「%s」として出します。"
                % (row_number, case_type, TYPE_FALLBACK)
            )
            case_type = TYPE_FALLBACK
        if not case_type:
            warn(
                "%d行目：分類が空です。「%s」として出します。" % (row_number, TYPE_FALLBACK)
            )
            case_type = TYPE_FALLBACK

        items.append({
            "order": parse_order(cell(row, COL_ORDER), row_number),
            "category": category,
            "type": case_type,
            "before": before,
            "after": after,
            "location": cell(row, COL_LOCATION),
            "period": cell(row, COL_PERIOD),
            "cost": cell(row, COL_COST),
            "building": cell(row, COL_BUILDING),
            "problem": cell(row, COL_PROBLEM),
            "work": cell(row, COL_WORK),
            "change": cell(row, COL_CHANGE),
            "comment": cell(row, COL_COMMENT),
            "link": check_link(cell(row, COL_LINK), row_number),
            "row": row_number,
        })

    if not items:
        die(
            "掲載できる行が1件もありませんでした。"
            "「公開」「施主承諾」の✓と、写真の欄を確認してください。"
        )

    # 表示順の小さい順。同じ数字どうしは台帳の行の順のまま（安定ソート）
    items.sort(key=lambda item: item["order"])
    return items


def build_js(items, ledger_url):
    lines = []
    lines.append("/* ============================================================")
    lines.append("   施工事例のデータ")
    lines.append("")
    lines.append("   ■ このファイルは自動で作られています。直接編集しないでください。")
    lines.append("     次回の自動反映のときに、ここでの手直しは消えてしまいます。")
    lines.append("")
    lines.append("   ■ 内容を直すところ：施工事例台帳（スプレッドシート）")
    if ledger_url:
        lines.append("     " + ledger_url)
    lines.append("")
    lines.append("   ■ 作り直しているもの：tools/施工事例台帳_生成.py")
    lines.append("     （.github/workflows/news-from-sheet.yml が定期的に実行します）")
    lines.append("     /works/ のカードも、続けて tools/施工事例一覧作成.py が作り直します。")
    lines.append("   ============================================================ */")
    lines.append("")
    lines.append("const CASE_ITEMS = [")

    for index, item in enumerate(items):
        lines.append(
            "  // ---- %d件目（台帳 %d行目） ----" % (index + 1, item["row"])
        )
        lines.append("  {")
        lines.append('    category: "%s",' % js_string(item["category"]))
        lines.append('    type:     "%s",' % js_string(item["type"]))
        lines.append('    before: "%s",' % js_string(item["before"]))
        lines.append('    after:  "%s",' % js_string(item["after"]))
        lines.append(
            '    spec:   { location: "%s", period: "%s", cost: "%s", building: "%s" },'
            % (
                js_string(item["location"]),
                js_string(item["period"]),
                js_string(item["cost"]),
                js_string(item["building"]),
            )
        )
        lines.append("    detail: {")
        lines.append('      problem: "%s",' % js_string(item["problem"]))
        lines.append('      work:    "%s",' % js_string(item["work"]))
        lines.append('      change:  "%s",' % js_string(item["change"]))
        lines.append('      comment: "%s"' % js_string(item["comment"]))
        lines.append("    },")
        lines.append('    link: "%s"' % js_string(item["link"]))
        lines.append("  }," if index < len(items) - 1 else "  }")

    lines.append("];")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="施工事例台帳から cases.js を作り直します。")
    parser.add_argument("--csv", required=True, help="台帳のCSV（ファイルパス、または公開URL）")
    parser.add_argument("--out", default="cases.js", help="書き出し先（既定: cases.js）")
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
