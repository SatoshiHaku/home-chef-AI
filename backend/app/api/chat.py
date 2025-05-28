from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..models.models import Ingredient, Recipe, IngredientCreate, IngredientUpdate
from ..utils.sheets import read_sheet, write_sheet, update_sheet, delete_sheet
from ..services.llm_service import get_llm_response
import os
from datetime import datetime, timedelta

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    message: str
    action: Optional[dict] = None

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
    """チャットメッセージを処理し、適切なアクションを実行"""
    try:
        # 最後のユーザーメッセージを取得
        user_message = next((msg.content for msg in reversed(request.messages) 
                           if msg.role == "user"), None)
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # LLMにメッセージを送信して意図を解析
        llm_response = await get_llm_response(request.messages)
        
        # LLMの応答に基づいてアクションを実行
        action = None
        if "action" in llm_response:
            action = llm_response["action"]
            if action["type"] == "add_ingredient":
                # 単一の材料の追加
                ingredient = IngredientCreate(
                    name=action["data"]["name"],
                    quantity=action["data"]["quantity"],
                    unit=action["data"]["unit"],
                    category=action["data"]["category"],
                    expiry_date=datetime.fromisoformat(action["data"]["expiry_date"]) 
                    if "expiry_date" in action["data"] else None
                )
                # 材料を追加する処理を実行
                values = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A2:A")
                new_id = len(values) + 1
                new_row = [
                    new_id,
                    ingredient.name,
                    ingredient.quantity,
                    ingredient.unit,
                    ingredient.expiry_date.isoformat() if ingredient.expiry_date else "",
                    datetime.now().isoformat(),
                    ingredient.category
                ]
                write_sheet(os.getenv("GOOGLE_SHEETS_ID"), f"Ingredients!A{new_id+1}", [new_row])

            elif action["type"] == "add_multiple_ingredients":
                # 複数の材料の追加
                values = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A2:A")
                start_id = len(values) + 1
                new_rows = []
                
                for i, ingredient_data in enumerate(action["data"]):
                    ingredient = IngredientCreate(
                        name=ingredient_data["name"],
                        quantity=ingredient_data["quantity"],
                        unit=ingredient_data["unit"],
                        category=ingredient_data["category"],
                        expiry_date=datetime.fromisoformat(ingredient_data["expiry_date"]) 
                        if "expiry_date" in ingredient_data else None
                    )
                    new_rows.append([
                        start_id + i,
                        ingredient.name,
                        ingredient.quantity,
                        ingredient.unit,
                        ingredient.expiry_date.isoformat() if ingredient.expiry_date else "",
                        datetime.now().isoformat(),
                        ingredient.category
                    ])
                
                # 複数の材料を一度に追加
                write_sheet(os.getenv("GOOGLE_SHEETS_ID"), 
                           f"Ingredients!A{start_id+1}:G{start_id+len(new_rows)}", 
                           new_rows)

            elif action["type"] == "update_ingredient":
                # 材料の更新
                ingredient_name = action["data"]["name"]
                result = find_ingredient_by_name(ingredient_name)
                if not result:
                    raise HTTPException(status_code=404, detail=f"材料 '{ingredient_name}' が見つかりません")
                
                row_id, current_ingredient = result
                
                # 更新データの準備
                update_data = {}
                if "expiry_date" in action["data"]:
                    # 日付をフォーマット
                    formatted_date = format_date(action["data"]["expiry_date"])
                    update_data["expiry_date"] = datetime.strptime(formatted_date, "%Y-%m-%d")
                
                # 材料を更新
                updated_ingredient = current_ingredient.copy(update=update_data)
                updated_row = [
                    current_ingredient.id,
                    updated_ingredient.name,
                    updated_ingredient.quantity,
                    updated_ingredient.unit,
                    updated_ingredient.expiry_date.strftime("%Y-%m-%d") if updated_ingredient.expiry_date else "",
                    datetime.now().isoformat(),
                    updated_ingredient.category
                ]
                update_sheet(os.getenv("GOOGLE_SHEETS_ID"), 
                           f"Ingredients!A{row_id+1}", [updated_row])

            elif action["type"] == "delete_ingredient":
                # 材料の削除
                ingredient_name = action["data"]["name"]
                result = find_ingredient_by_name(ingredient_name)
                if not result:
                    raise HTTPException(status_code=404, detail=f"材料 '{ingredient_name}' が見つかりません")
                
                row_id, _ = result
                delete_sheet(os.getenv("GOOGLE_SHEETS_ID"), 
                           f"Ingredients!A{row_id+1}:G{row_id+1}")

            elif action["type"] == "list_ingredients":
                # 材料一覧の取得
                values = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Ingredients!A2:G")
                ingredients = []
                for row in values:
                    ingredient = Ingredient(
                        id=int(row[0]),
                        name=row[1],
                        quantity=float(row[2]),
                        unit=row[3],
                        expiry_date=datetime.fromisoformat(row[4]) if row[4] else None,
                        updated_at=datetime.fromisoformat(row[5]),
                        category=row[6]
                    )
                    ingredients.append(ingredient)
                
                # 材料一覧をメッセージに含める
                ingredient_list = "\n".join([
                    f"- {ing.name}: {ing.quantity}{ing.unit} ({ing.category})"
                    + (f" 消費期限: {ing.expiry_date.strftime('%Y-%m-%d')}" if ing.expiry_date else "")
                    for ing in ingredients
                ])
                llm_response["message"] = f"現在の材料一覧です：\n{ingredient_list}"

            elif action["type"] == "search_recipes":
                # レシピの検索
                recipes = read_sheet(os.getenv("GOOGLE_SHEETS_ID"), "Recipes!A2:G")
                # 検索条件に基づいてレシピをフィルタリング
                # 結果をLLMの応答に含める

        return ChatResponse(
            message=llm_response["message"],
            action=action
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 