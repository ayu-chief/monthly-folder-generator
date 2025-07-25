
# Google Drive Monthly Folder Generator

指定した年・月の平日（祝日を除く）に基づいて、Google Drive に日別フォルダ（例：`20250801_`）を自動で作成するツールです。

## 🔧 使用方法

1. Google Cloud Console でサービスアカウントを作成し、JSON キーを取得
2. `service_account.json` としてルートに保存（このファイルは `.gitignore` 済み）
3. 対象の親フォルダにサービスアカウントを「編集者」として共有
4. パッケージをインストール

```bash
pip install -r requirements.txt
```

5. `main.py` 内の `YEAR`, `MONTH`, `PARENT_FOLDER_ID` を指定し実行

```bash
python main.py
```

## 🗓️ 特徴

- 日本の祝日カレンダーAPIで祝日を除外
- 月フォルダがなければ自動作成
- 日付フォルダ形式は `YYYYMMDD_`

## 📂 フォルダ構成例（2025年8月）

```
📁 202508
├── 20250801_/
├── 20250804_/
├── 20250805_/
└── ...
```
