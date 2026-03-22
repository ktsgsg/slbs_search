# subject_info.html の辞書化データ仕様

このドキュメントは、infomation_exact.py の以下の関数が返すデータ形式を説明します。

- parse_subject_info_html(html_content, subject_id=None)
- parse_subject_info_file(file_path, subject_id=None)
- save_subject_info_json_from_html(html_content, output_json_path, subject_id=None, indent=2)
- save_subject_info_json(input_html_path, output_json_path, subject_id=None, indent=2)

## 返却形式

以下の形式で返します。

{
  "id": "111254_01101",
  "fields": {
    "科目名": "基礎演習1",
    "担当者氏名": "山岡 航",
    "年次": "1年次",
    "更新日時": "2024-12-26 18:07:23.591"
  },
  "lists": {
    "授業計画": {
      "headers": ["項目欄", "内容欄"],
      "items": [
        {"no": 1, "項目欄": "【第1週】オリエンテーション", "内容欄": "授業の進め方についての説明、自己紹介"},
        {"no": 2, "項目欄": "【第2週】法律学……の前に", "内容欄": "論理的思考方法の練習"}
      ]
    },
    "テキスト": {
      "headers": ["書籍名", "著者", "出版社"],
      "items": [
        {"no": 1, "書籍名": "法律学習マニュアル〔第4版〕", "著者": "弥永真生", "出版社": "有斐閣"}
      ]
    }
  }
}

## 各キーの意味

- id:
  - 関数引数で渡した任意ID。
  - subject_id を渡さなかった場合は null。
- fields:
  - 左列ラベルに対応する通常テキスト項目。
  - 例: 科目名, 担当者氏名, 到達目標, 更新日時。
- lists:
  - 値セル内のネスト表から検出したリスト項目。
  - 例: 授業計画, テキスト, 参考文献。

## リスト検出ルール

- 値セル内にネストされた表があり、行頭が 1. 2. のような連番の行をリスト要素として検出。
- ヘッダー行に 【...】 がある場合は、その見出し名をキーとして使用。
- ヘッダー列数と値列数が一致しない場合は col1, col2 のような汎用キーを使用。

## JSON保存関数の挙動

- save_subject_info_json_from_html:
  - HTML文字列を解析し、JSONファイルに保存。
- save_subject_info_json:
  - HTMLファイルを読み込んで解析し、JSONファイルに保存。
- どちらも保存した辞書データを戻り値として返す。
- JSON出力は ensure_ascii=False で保存されるため、日本語はそのまま出力される。
