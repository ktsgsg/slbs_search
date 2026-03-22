# Meilisearch 検索エンジン仕様書

## 1. 目的

本仕様書は、シラバス詳細データを Meilisearch で高速検索できるようにするための要件と設計を定義する。

- 対象データ: `parse_subject_info_html` / `save_subject_info_json` で生成された辞書データ
- 主な利用目的: キーワード検索、担当者検索、年度・学期絞り込み、講義コード検索

## 2. 対象範囲

### 2.1 対象

- シラバス1件を1ドキュメントとしてインデックス登録
- 日本語テキストの全文検索
- 属性フィルタ検索
- ソート

### 2.2 非対象

- 認可・認証機能
- UIデザイン詳細
- 分散クラスタ構成

## 3. 入力データ仕様

### 3.1 元データ形式

元データは以下を前提とする。

- `id`: 任意ID（推奨: `kougicd_crclumcd`）
- `fields`: 通常項目（科目名、担当者氏名、講義学期など）
- `lists`: 表形式項目（授業計画、テキスト、参考文献など）

### 3.2 URL由来項目

URLから以下を抽出して付与する。

- `kougicd`: `value(kougicd)`
- `risyunen`: `value(risyunen)`
- `semekikn`: `value(semekikn)`
- `crclumcd`: `value(crclumcd)`

## 4. インデックス設計

### 4.1 インデックス名

- `syllabus`

### 4.2 Primary Key

- `id`

### 4.3 登録ドキュメント構造

以下を最小構成とする。

```json
{
  "id": "111254_01101",
  "kougicd": "111254",
  "risyunen": "2025",
  "semekikn": "1",
  "crclumcd": "01101",
  "科目名": "基礎演習1",
  "担当者氏名": "山岡 航",
  "講義学期": "前期",
  "年次": "1年次",
  "更新日時": "2024-12-26 18:07:23.591",
  "授業計画_text": "【第1週】... 【第2週】...",
  "テキスト_text": "法律学習マニュアル〔第4版〕 弥永真生 有斐閣",
  "参考文献_text": "授業で適宜紹介します。",
  "full_text": "科目名 担当者 授業計画 到達目標 ... を連結した文字列",
  "fields": {},
  "lists": {}
}
```

### 4.4 正規化ルール

登録前に以下を行う。

- 改行・連続空白を単一スペースへ正規化
- 文字列を NFKC 正規化
- リスト項目は検索用に結合文字列（`*_text`）を別途作成

## 5. Meilisearch 設定

### 5.1 searchableAttributes

優先順で以下を設定する。

1. `科目名`
2. `担当者氏名`
3. `授業計画_text`
4. `テキスト_text`
5. `参考文献_text`
6. `full_text`

### 5.2 filterableAttributes

- `risyunen`
- `semekikn`
- `kougicd`
- `crclumcd`
- `講義学期`
- `年次`
- `担当者氏名`

### 5.3 sortableAttributes

- `更新日時`
- `科目名`

### 5.4 displayedAttributes

- `id`
- `kougicd`
- `科目名`
- `担当者氏名`
- `講義学期`
- `年次`
- `更新日時`
- `fields`
- `lists`

### 5.5 typoTolerance

- `disableOnAttributes`: `id`, `kougicd`

理由: コード検索は誤字補正不要で、厳密一致を優先するため。

## 6. 登録フロー

1. HTML取得
2. 解析（`parse_subject_info_html`）
3. URL情報抽出（`extract_kougicd_from_url` など）
4. Meilisearch用ドキュメントへ変換
5. バルク登録（`add_documents`）
6. タスク完了確認

## 7. 検索要件

### 7.1 キーワード検索

- 入力: 自由語句（例: `基礎演習 法学入門`）
- 対象: `searchableAttributes`

### 7.2 フィルタ検索

- 例: `risyunen = 2025 AND semekikn = 1`
- 例: `kougicd = 111254`

### 7.3 ソート

- 更新日時降順
- 科目名昇順

## 8. API要件（アプリ側）

### 8.1 検索API

- エンドポイント例: `GET /search`
- パラメータ:
  - `q`: 検索語
  - `risyunen`
  - `semekikn`
  - `kougicd`
  - `sort`
  - `offset`, `limit`

### 8.2 レスポンス

- `hits`
- `estimatedTotalHits`
- `processingTimeMs`
- `query`

## 9. 非機能要件

- 1クエリあたりの応答目標: 300ms 以内（ローカル環境）
- インデックス再作成を可能にする（全件再投入手順を用意）
- 失敗時リトライ（指数バックオフ）を実装

## 10. 運用要件

- 年度更新時に差分または全件再投入
- スキーマ変更時はインデックスを新規作成して切り替え
- 検索ログを収集し、`searchableAttributes` の順序を調整

## 11. 受け入れ基準

以下を満たしたらリリース可能とする。

1. 任意キーワードで関連授業が上位表示される
2. `kougicd` フィルタで対象授業を一意に特定できる
3. `risyunen` と `semekikn` で絞り込み可能
4. 10,000件規模で検索応答が目標値内
5. 再インデックス手順が実行できる

## 12. 実装順序（推奨）

1. ドキュメント変換処理の実装
2. Meilisearch 初期設定投入
3. バルク登録処理
4. 検索API実装
5. 評価・調整（属性順序、同義語、ストップワード）
