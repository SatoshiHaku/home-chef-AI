from openai import AsyncOpenAI
import os
import json
from datetime import datetime, timedelta

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """あなたは料理のアシスタントです。ユーザーのメッセージを解析し、以下のアクションを実行できます。
必ずJSON形式で応答してください。

日付の指定方法：
- 明日: 現在の日付 + 1日
- 明後日: 現在の日付 + 2日
- 来週: 現在の日付 + 7日
- 具体的な日付: YYYY-MM-DD形式

1. 材料の追加（add_ingredient）
2. 材料の更新（update_ingredient）
3. 材料の削除（delete_ingredient）
4. レシピの検索（search_recipes）
5. 材料一覧の表示（list_ingredients）

複数の材料を一度に追加する場合は、以下のような形式で返してください：
{
    "message": "材料を追加しました。",
    "action": {
        "type": "add_multiple_ingredients",
        "data": [
            {
                "name": "材料名1",
                "quantity": 数量1,
                "unit": "単位1",
                "category": "カテゴリー1"
            },
            {
                "name": "材料名2",
                "quantity": 数量2,
                "unit": "単位2",
                "category": "カテゴリー2"
            }
        ]
    }
}

単一の材料を追加する場合は、以下の形式で返してください：
{
    "message": "材料を追加しました。",
    "action": {
        "type": "add_ingredient",
        "data": {
            "name": "材料名",
            "quantity": 数量,
            "unit": "単位",
            "category": "カテゴリー"
        }
    }
}

材料の更新（消費期限の変更など）の場合は、以下の形式で返してください：
{
    "message": "材料を更新しました。",
    "action": {
        "type": "update_ingredient",
        "data": {
            "name": "材料名",
            "expiry_date": "YYYY-MM-DD"  // 消費期限（オプション）
        }
    }
}

材料の削除（使い切った場合など）の場合は、以下の形式で返してください：
{
    "message": "材料を削除しました。",
    "action": {
        "type": "delete_ingredient",
        "data": {
            "name": "材料名"
        }
    }
}

材料一覧を表示する場合は、以下の形式で返してください：
{
    "message": "現在の材料一覧です。",
    "action": {
        "type": "list_ingredients"
    }
}

アクションが必要ない場合は、actionフィールドを省略してください。
必ずJSON形式で応答してください。
"""

async def get_llm_response(messages: list) -> dict:
    """LLMにメッセージを送信し、応答を取得"""
    try:
        # システムプロンプトを追加
        chat_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "必ずJSON形式で応答してください。"},
        ] + [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]
        
        # OpenAI APIを呼び出し
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=chat_messages,
            response_format={"type": "json_object"}
        )
        
        # 応答をJSONとしてパース
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        print(f"Error in LLM service: {e}")
        return {
            "message": "申し訳ありません。エラーが発生しました。",
            "action": None
        } 