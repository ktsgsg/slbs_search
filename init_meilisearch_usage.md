# init_meilisearch.py 使い方

このドキュメントは、Meilisearch の初期化と JSON 一括登録を行うスクリプト `init_meilisearch.py` の実行手順を説明します。

## 1. できること

- インデックス作成（未作成時のみ）
- 仕様に沿った settings の投入
- 指定フォルダ配下の JSON を再帰的に探索
- 全 JSON を自動で一括登録

## 2. 前提

- Meilisearch が起動済みであること
- Python 依存関係がインストール済みであること
- 各 JSON ドキュメントに `id` があること

`id` がないドキュメントは自動スキップされます。

## 3. Meilisearch の起動

プロジェクトルートで実行:

```bash
docker compose up -d
```

疎通確認:

```bash
curl http://127.0.0.1:7700/health
```

## 4. 実行方法

基本形:

```bash
uv run python init_meilisearch.py <target_dir>
```

例:

```bash
uv run python init_meilisearch.py subjects_2025
```

## 5. オプション

```text
positional arguments:
  target_dir            JSON ファイルを含む対象フォルダ

optional arguments:
  --host                Meilisearch URL（既定: http://127.0.0.1:7700）
  --api-key             Meilisearch APIキー（既定: 環境変数 MEILI_MASTER_KEY）
  --index               インデックス名（既定: syllabus）
  --batch-size          1回に登録する件数（既定: 500）
  --no-wait             非同期タスク完了待ちをしない
```

## 6. 実行例

ホストとインデックスを指定:

```bash
uv run python init_meilisearch.py subjects_2025 \
  --host http://127.0.0.1:7700 \
  --index syllabus
```

API キーを指定:

```bash
uv run python init_meilisearch.py subjects_2025 --api-key YOUR_MASTER_KEY
```

バッチサイズを変更:

```bash
uv run python init_meilisearch.py subjects_2025 --batch-size 300
```

完了待ちを無効化:

```bash
uv run python init_meilisearch.py subjects_2025 --no-wait
```

## 7. 入力 JSON の想定

- 1ファイルに1件の辞書
- 1ファイルに複数件の配列

どちらにも対応しています。

最小例:

```json
{
  "id": "111254_01101",
  "科目名": "基礎演習1",
  "担当者氏名": "山岡 航",
  "full_text": "..."
}
```

## 8. 実行時ログ

主な表示:

- `Index creation task queued: ...`
- `Settings update task queued: ...`
- `Discovered JSON files: ...`
- `Valid documents to upload: ...`
- `Upload tasks queued: ...`
- `Completed`
- `Skipped JSON files (no valid docs): ...`

## 9. よくあるエラー

### target_dir が存在しない

- メッセージ: `Target directory does not exist or is not a directory`
- 対応: パス指定を確認する

### API key エラー

- 対応: `--api-key` か環境変数 `MEILI_MASTER_KEY` を確認する

### 登録件数が 0

- `id` 欠落ドキュメントはスキップされる
- JSON 形式（辞書または辞書配列）になっているか確認する

## 10. 推奨手順

1. `docker compose up -d` で Meilisearch を起動
2. 小さなフォルダで試験投入
3. 問題なければ本番対象フォルダを投入
4. 必要なら `--batch-size` を調整
