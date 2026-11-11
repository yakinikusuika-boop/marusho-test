# -*- coding: utf-8 -*-
"""
お知らせ台帳（Googleスプレッドシートの公開CSV）を1ファイルに取り寄せるスクリプト。

  使い方（URLは環境変数から受け取る。引数には書かない）:
      NEWS_SHEET_CSV_URL="https://docs.google.com/.../pub?output=csv" \
        python tools/お知らせ台帳_取り寄せ.py --out work/ledger_raw.csv

  なぜ curl ではなくこれを使うのか
    1. 失敗の理由が分かるようにするため。curl だと「失敗した」しか残らないが、
       これなら「HTTP 401」「HTTPが返ってきた」まで記録できる。
       実際、2026-11-11 の不具合はこのログで 401 と判明した。
    2. curl は URL に改行やタブが混ざっていると、それだけで取得できない
       （exit 3: Malformed input）。GitHub の Secret は貼り付けのときに
       末尾の改行が入りやすい。Python の urllib は改行・タブを自動で取り除くうえ、
       ここでは自分でも前後の空白と改行・タブを落としている。

  安全のための決めごと
    ・取得できなかった／中身が空だったときは終了コード 1。出力ファイルは作らない。
      → 呼び出し側（ワークフロー）はここで止まるので、news.js は書き換わらない。
    ・エラー文には URL を一切出さない。台帳のURLはログに残さない。

  標準ライブラリだけで動く。
"""

import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.request

ENV_NAME = "NEWS_SHEET_CSV_URL"
USER_AGENT = "marusho-news-builder"
TIMEOUT_SECONDS = 60
ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5


def die(message):
    """URLを出さずに失敗を知らせて終わる。"""
    sys.stderr.write("::error::%s\n" % message)
    sys.exit(1)


def clean_url(raw):
    """前後の空白と、途中に混ざった改行・タブを取り除く。"""
    return re.sub(r"[\r\n\t]", "", (raw or "").strip())


def url_kind(url):
    """URLの種類だけを言う。URL自体はログに出さない。"""
    if "/spreadsheets/d/e/" in url and "/pub" in url:
        return "ウェブに公開（pub）"
    if "/gviz/" in url:
        return "gviz ※共有設定しだいで匿名では読めません。「ウェブに公開」のURLを使ってください"
    if "/export" in url:
        return "export ※共有設定しだいで匿名では読めません。「ウェブに公開」のURLを使ってください"
    return "その他"


def fetch(url):
    """台帳のCSVを取ってくる。失敗したら数秒おいて繰り返す。"""
    last_error = ""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            # 404・401 などは繰り返しても直らないので、その場で諦める
            last_error = "HTTP %s %s" % (error.code, error.reason)
            if error.code in (401, 403):
                last_error += (
                    "（匿名では読めない状態です。台帳の「ファイル → 共有 → ウェブに公開」が"
                    "止まっていないか確認してください）"
                )
            if error.code < 500:
                break
        except Exception as error:  # 通信の失敗・時間切れなど
            last_error = type(error).__name__
        if attempt < ATTEMPTS:
            sys.stderr.write(
                "::warning::台帳の取り寄せに失敗しました（%s）。%d秒おいて%d回目を試します。\n"
                % (last_error, RETRY_WAIT_SECONDS, attempt + 1)
            )
            time.sleep(RETRY_WAIT_SECONDS)
    die("台帳を取り寄せられませんでした（%s）。news.js は書き換えていません。" % last_error)


def main():
    parser = argparse.ArgumentParser(
        description="台帳の公開CSVを取り寄せてファイルに保存する"
    )
    parser.add_argument("--out", required=True, help="保存先（例: work/ledger_raw.csv）")
    parser.add_argument(
        "--env-name",
        default=ENV_NAME,
        help="台帳のURLが入っている環境変数の名前（既定: %s。"
        "施工事例台帳は CASES_SHEET_CSV_URL を指定）" % ENV_NAME,
    )
    args = parser.parse_args()

    env_name = args.env_name
    url = clean_url(os.environ.get(env_name))
    if not url:
        die(
            "%s が未設定です。リポジトリの Secrets に台帳のCSV URLを登録してください。"
            % env_name
        )
    if not re.match(r"^https://", url, re.I):
        die(
            "%s が https:// で始まっていません。台帳のCSV URLを登録し直してください。"
            % env_name
        )

    print("URLの形: %s" % url_kind(url), flush=True)

    raw = fetch(url)
    if not raw.strip():
        die("台帳が空でした。news.js は書き換えていません。")
    if raw.lstrip()[:1] == b"<":
        die(
            "台帳のCSVではなく、HTMLのページが返ってきました。"
            "「ウェブに公開」のURL（.../pub?...output=csv）か確認してください。"
        )

    folder = os.path.dirname(os.path.abspath(args.out))
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(args.out, "wb") as handle:
        handle.write(raw)

    print("台帳を取り寄せました（%d バイト）" % len(raw), flush=True)


if __name__ == "__main__":
    main()
