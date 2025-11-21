# slbs_search

ローカルスクリプト: 名城大学のシラバス検索ページを自動で取得・解析するための簡易ツール集合です。

**重要な注意**: このスクリプトはサーバーへ繰り返しリクエストを送信します。短時間で大量に実行するとサーバーに負荷をかけ、サービス停止や利用制限につながる恐れがあります。頻度を抑え、責任を持って利用してください。

## 目的
- 指定ページの HTML を取得し、ページ内の hidden `timestamp` を抽出して POST に利用します。
- `Set-Cookie` ヘッダからセッションを取得し、POST に渡して次ページ以降を巡回します。

## 必要環境
- macOS / Linux / Windows (Python 3.8+ 推奨)
- Python パッケージ: `requests`, `beautifulsoup4`, `pyOpenSSL`, `cryptography`, `certifi`

依存パッケージは `requirements.txt` を使ってインストールしてください。

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 使い方（基本）
1. リポジトリをクローンまたはダウンロードします。
2. 仮想環境を作ることを推奨します（例: `python -m venv .venv`、`source .venv/bin/activate`）。
3. 依存パッケージをインストールします（上のコマンド参照）。
4. `main.py` を実行します:

```bash
python main.py
```

実行すると、初回に GET でページを取得し、HTML 内の `input[name="timestamp"]` を解析して POST パラメータを作成、続けて POST を実行して結果を `response.html` に保存します。

## 設定・拡張
- `main.py` 内の `url` を解析対象の URL に変更できます（デフォルトは名城大学の検索エンドポイント）。
- クライアント証明書が必要な場合は、pyOpenSSL を利用して PEM にダンプし `requests` の `cert=(certfile,keyfile)` に渡す方法を利用しています（`main.py` にサンプルコードあり）。

## 出力
- `response.html` : POST 応答の HTML を保存します。
- 標準出力に処理ログ（タイムスタンプ抽出の成功/失敗や POST の成否）を出力します。

## 利用上の注意（再掲）
- サイトの利用規約や robots.txt を必ず確認してください。許可されていない取得は行わないでください。
- 短時間に大量のアクセスを行うとサーバーに負荷がかかります。必ず間隔を空け（例: 数秒〜数十秒）、必要最低限の回数で実行してください。
- 研究目的や自動化で利用する場合でも、可能であれば運営に事前連絡することを強く推奨します。

## トラブルシュート
- TLS / SSL に関するエラーが出る場合、`pyOpenSSL` を `urllib3` に注入することで改善することがあります（`from urllib3.contrib import pyopenssl; pyopenssl.inject_into_urllib3()` を実行）。
- それでも接続できない場合は、システムの OpenSSL バージョンや Python のビルド状況を確認してください。最終手段として `curl --tlsv1.2` を用いる回避策を `main.py` に組み込むことも可能です。

## ライセンス
このリポジトリでは特にライセンスを明記していません。用途に応じて適切なライセンスを追加してください。

