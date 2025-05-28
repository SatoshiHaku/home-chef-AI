from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router as api_router
from .api.chat import router as chat_router
from dotenv import load_dotenv
from .utils.sheets import initialize_sheets
import os

# 環境変数の読み込み
load_dotenv()

app = FastAPI(title="Home Chef AI API")

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの追加
app.include_router(api_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Home Chef AI API"}

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if spreadsheet_id:
        try:
            initialize_sheets(spreadsheet_id)
        except Exception as e:
            print(f"Failed to initialize sheets: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 