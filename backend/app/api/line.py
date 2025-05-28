from fastapi import APIRouter, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, MessageEvent, TextMessage
import os
import requests

router = APIRouter()

# LINE APIの設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@router.post("/line/webhook")
async def line_webhook(request: Request):
    """LINE Messaging APIのWebhookエンドポイント"""
    # リクエストヘッダーからX-Line-Signatureを取得
    signature = request.headers.get("X-Line-Signature", "")
    
    # リクエストボディを取得
    body = await request.body()
    
    try:
        # 署名を検証
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    return {"status": "ok"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """テキストメッセージのハンドラー"""
    # ユーザーからのメッセージを取得
    user_message = event.message.text
    
    # チャットAPIを呼び出し
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={"messages": [{"role": "user", "content": user_message}]}
    )
    
    # レスポンスを取得
    data = response.json()
    
    # LINEにメッセージを送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=data["message"])
    ) 