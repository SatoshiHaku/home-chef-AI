from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..models.models import Ingredient, Recipe, IngredientCreate, IngredientUpdate
from ..utils.sheets import read_sheet, write_sheet, update_sheet, delete_sheet
from ..services.llm_service import get_llm_response
import os
from datetime import datetime, timedelta
import json

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    message: str
    action: Optional[dict] = None
    ingredients: Optional[List[dict]] = None
    recipes: Optional[List[dict]] = None

def find_ingredient_by_name(name: str) -> Optional[tuple[int, Ingredient]]:
    """材料名から材料を検索"""
    values = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A2:G")
    for i, row in enumerate(values, start=1):
        if row[1].lower() == name.lower():
            ingredient = Ingredient(
                id=int(row[0]),
                name=row[1],
                quantity=float(row[2]),
                unit=row[3],
                expiry_date=datetime.fromisoformat(row[4]) if row[4] else None,
                updated_at=datetime.fromisoformat(row[5]),
                category=row[6]
            )
            return i, ingredient
    return None

def format_date(date_str: str) -> str:
    """日付文字列をフォーマット"""
    try:
        # 日付文字列をパース
        date = datetime.strptime(date_str, "%Y-%m-%d")
        # YYYY-MM-DD形式にフォーマット
        return date.strftime("%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"無効な日付形式です: {date_str}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # メッセージを処理
        messages = [{"role": "user", "content": msg.content} for msg in request.messages]
        
        # LLMからの応答を取得
        llm_response = get_llm_response(messages)
        print(f"LLM Response: {llm_response}")  # デバッグ用
        
        # LLMの応答からJSONを抽出
        import re
        import json
        
        # コードブロック内のJSONを抽出
        json_match = re.search(r'```json\n(.*?)\n```', llm_response["message"], re.DOTALL)
        if json_match:
            try:
                response = json.loads(json_match.group(1))
                print(f"Parsed JSON: {response}")  # デバッグ用
            except json.JSONDecodeError as e:
                print(f"JSONのパースに失敗: {str(e)}")  # デバッグ用
                raise HTTPException(
                    status_code=500,
                    detail=f"LLMの応答のパースに失敗しました: {str(e)}"
                )
        else:
            # JSONが見つからない場合は、メッセージのみを返す
            response = {"message": llm_response["message"]}
        
        # アクションの処理
        if "action" in response:
            action = response["action"]
            action_type = action.get("type")
            action_data = action.get("data", {})
            
            if action_type == "add_ingredient":
                try:
                    # 新しい材料IDを生成
                    ingredients = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A:G")
                    new_id = str(len(ingredients))  # ヘッダー行を考慮
                    
                    # 現在の日時を取得
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 材料データを準備
                    ingredient_data = [
                        [
                            new_id,
                            action_data["name"],
                            str(action_data["quantity"]),
                            action_data["unit"],
                            "",  # expiry_date
                            current_time,
                            action_data.get("category", "")
                        ]
                    ]
                    
                    print(f"Writing ingredient data: {ingredient_data}")  # デバッグ用
                    
                    # スプレッドシートに書き込み
                    write_sheet(
                        os.getenv("GOOGLE_SHEETS_ID"),
                        "Ingredients!A:G",
                        ingredient_data
                    )
                    
                    # 材料一覧を取得して返す
                    ingredients = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A:G")
                    if len(ingredients) > 1:  # ヘッダー行を除く
                        response["ingredients"] = [
                            {
                                "name": row[1],
                                "quantity": float(row[2]),
                                "unit": row[3],
                                "category": row[6]
                            }
                            for row in ingredients[1:]  # ヘッダー行をスキップ
                        ]
                    
                    response["message"] = f"{action_data['name']} {action_data['quantity']}{action_data['unit']}を追加しました。"
                except Exception as e:
                    print(f"材料追加中にエラーが発生: {str(e)}")  # デバッグ用
                    raise HTTPException(
                        status_code=500,
                        detail=f"材料の追加中にエラーが発生しました: {str(e)}"
                    )
            
            elif action_type == "list_ingredients":
                try:
                    ingredients = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A:G")
                    if len(ingredients) > 1:  # ヘッダー行を除く
                        response["ingredients"] = [
                            {
                                "name": row[1],
                                "quantity": float(row[2]),
                                "unit": row[3],
                                "category": row[6]
                            }
                            for row in ingredients[1:]  # ヘッダー行をスキップ
                        ]
                        response["message"] = "現在の材料一覧です。"
                    else:
                        response["message"] = "現在、材料は登録されていません。"
                except Exception as e:
                    print(f"材料一覧取得中にエラーが発生: {str(e)}")  # デバッグ用
                    raise HTTPException(
                        status_code=500,
                        detail=f"材料一覧の取得中にエラーが発生しました: {str(e)}"
                    )
            
            elif action_type == "update_ingredient":
                try:
                    ingredients = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A:G")
                    for i, row in enumerate(ingredients[1:], 1):  # ヘッダー行をスキップ
                        if row[1] == action_data["name"]:
                            row[2] = str(action_data["quantity"])
                            row[3] = action_data["unit"]
                            row[5] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            write_sheet(
                                os.getenv("GOOGLE_SHEETS_ID"),
                                f"Ingredients!A{i+1}:G{i+1}",
                                [row]
                            )
                            response["message"] = f"{action_data['name']}の数量を更新しました。"
                            break
                    else:
                        response["message"] = f"{action_data['name']}が見つかりませんでした。"
                except Exception as e:
                    print(f"材料更新中にエラーが発生: {str(e)}")  # デバッグ用
                    raise HTTPException(
                        status_code=500,
                        detail=f"材料の更新中にエラーが発生しました: {str(e)}"
                    )
            
            elif action_type == "delete_ingredient":
                try:
                    ingredients = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A:G")
                    for i, row in enumerate(ingredients[1:], 1):  # ヘッダー行をスキップ
                        if row[1] == action_data["name"]:
                            delete_sheet(
                                os.getenv("GOOGLE_SHEETS_ID"),
                                f"Ingredients!A{i+1}:G{i+1}"
                            )
                            response["message"] = f"{action_data['name']}を削除しました。"
                            break
                    else:
                        response["message"] = f"{action_data['name']}が見つかりませんでした。"
                except Exception as e:
                    print(f"材料削除中にエラーが発生: {str(e)}")  # デバッグ用
                    raise HTTPException(
                        status_code=500,
                        detail=f"材料の削除中にエラーが発生しました: {str(e)}"
                    )
            
            elif action_type == "search_recipes":
                try:
                    recipes = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Recipes!A:G")
                    query = action_data.get("query", "").lower()
                    matching_recipes = [
                        {
                            "name": row[1],
                            "ingredients": row[2],
                            "servings": row[3],
                            "url": row[4],
                            "category": row[5]
                        }
                        for row in recipes[1:]  # ヘッダー行をスキップ
                        if query in row[1].lower() or query in row[2].lower()
                    ]
                    if matching_recipes:
                        response["recipes"] = matching_recipes
                        response["message"] = f"「{query}」の検索結果です。"
                    else:
                        response["message"] = "条件に一致するレシピが見つかりませんでした。"
                except Exception as e:
                    print(f"レシピ検索中にエラーが発生: {str(e)}")  # デバッグ用
                    raise HTTPException(
                        status_code=500,
                        detail=f"レシピの検索中にエラーが発生しました: {str(e)}"
                    )
            
            elif action_type == "error":
                raise HTTPException(status_code=400, detail=action_data.get("message", "エラーが発生しました。"))
        
        return response
    
    except Exception as e:
        print(f"チャット処理中にエラーが発生: {str(e)}")  # デバッグ用
        raise HTTPException(
            status_code=500,
            detail=f"チャットの処理中にエラーが発生しました: {str(e)}"
        ) 