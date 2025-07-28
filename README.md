# UEDeliveryExport
UEDeliveryExportは、Uber Eatsの配達履歴ページを自動でスクレイピングし、CSVファイルとしてエクスポートするPythonツールです。

## 特長
- Uber Eats のウェブサイトから配達履歴を自動取得
- Selenium を使用してログイン～データ取得まで自動操作
- 日付・時刻・報酬額・詳細URLなどをCSVに保存
- デスクトップ用ブラウザ表示に対応

## 必要環境
- Python 3.8+
- Google Chrome（またはChromium系ブラウザ）
- ChromeDriver（ブラウザとバージョンを合わせてください）

## 使用前の準備
1. Uber Eatsドライバーアカウントのログイン情報を用意
2. config.pyにログイン情報を設定
```
EMAIL_ADDRESS = 'your-email@example.com'
PASSWORD = 'your-password'
```

## 使い方
```
python main.py
```

## 出力ファイル形式
- CSVファイル形式
- 文字エンコーディングはExcelで扱えるように「UTF-8 with BOM」

## ライセンス
This project uses the following open-source libraries:

- Selenium (Apache License 2.0): https://www.selenium.dev
- BeautifulSoup4 (MIT License): https://www.crummy.com/software/BeautifulSoup/

See LICENSE files for more details.

## 謝辞
このツールは学習・業務支援のために作成されています。
Uber 公式のAPI等ではないため、利用は自己責任でお願いいたします。
