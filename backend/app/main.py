from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from .api import chat
from .utils.sheets import initialize_sheets

# .envファイルの読み込み
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# 環境変数の確認
required_env_vars = [
    "OPENAI_API_KEY",
    "GOOGLE_SHEETS_ID",
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    try:
        # スプレッドシートの初期化
        initialize_sheets(os.getenv("GOOGLE_SHEETS_ID"))
        print("スプレッドシートの初期化が完了しました。")
    except Exception as e:
        print(f"スプレッドシートの初期化中にエラーが発生しました: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Home Chef AI API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 