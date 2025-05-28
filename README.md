# Home Chef AI

家にある材料を管理し、AIを活用してレシピを提案するアプリケーション

## 機能

- Google SheetsをDBとして使用した材料管理
- レシピデータベースの管理
- FastAPIによるバックエンドAPI
- iOS/iPadOSアプリによるフロントエンド
- チャットと音声による操作インターフェース
- AIによるレシピ提案

## セットアップ

### バックエンド

1. 必要なパッケージのインストール:
```bash
cd backend
pip install -r requirements.txt
```

2. Google Sheets APIの設定:
   - Google Cloud Consoleでプロジェクトを作成
   - Google Sheets APIを有効化
   - 認証情報を作成し、`credentials.json`として保存
   - `credentials.json`をbackendディレクトリに配置

3. サーバーの起動:
```bash
cd backend
uvicorn app.main:app --reload
```

### フロントエンド

1. Xcodeで`frontend/HomeChefAI`を開く
2. 必要なパッケージをインストール
3. ビルドして実行

## 環境変数

`.env`ファイルに以下の環境変数を設定:

```
GOOGLE_SHEETS_ID=your_spreadsheet_id
OPENAI_API_KEY=your_openai_api_key
```

## ライセンス

MIT License 