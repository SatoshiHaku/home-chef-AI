from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.models import Ingredient, IngredientCreate, IngredientUpdate, Recipe, RecipeIngredient
from ..utils.sheets import read_sheet, write_sheet, update_sheet, delete_sheet
import os
from datetime import datetime

router = APIRouter()

# 環境変数からスプレッドシートIDを取得
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_ID")

# 材料関連のエンドポイント
@router.get("/ingredients", response_model=List[Ingredient])
async def get_ingredients():
    """材料一覧を取得"""
    try:
        values = read_sheet(SPREADSHEET_ID, "Ingredients!A2:G")
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
        return ingredients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingredients", response_model=Ingredient)
async def create_ingredient(ingredient: IngredientCreate):
    """新しい材料を追加"""
    try:
        # 既存の材料を取得して新しいIDを生成
        values = read_sheet(SPREADSHEET_ID, "Ingredients!A2:A")
        new_id = len(values) + 1
        
        # 新しい材料を追加
        new_row = [
            new_id,
            ingredient.name,
            ingredient.quantity,
            ingredient.unit,
            ingredient.expiry_date.isoformat() if ingredient.expiry_date else "",
            datetime.now().isoformat(),
            ingredient.category
        ]
        write_sheet(SPREADSHEET_ID, f"Ingredients!A{new_id+1}", [new_row])
        
        return Ingredient(
            id=new_id,
            **ingredient.dict(),
            updated_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/ingredients/{ingredient_id}", response_model=Ingredient)
async def update_ingredient(ingredient_id: int, ingredient_update: IngredientUpdate):
    """材料を更新"""
    try:
        # 既存の材料を確認
        values = read_sheet(SPREADSHEET_ID, f"Ingredients!A{ingredient_id+1}:G{ingredient_id+1}")
        if not values:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # 既存の材料データを取得
        existing = values[0]
        current_ingredient = Ingredient(
            id=int(existing[0]),
            name=existing[1],
            quantity=float(existing[2]),
            unit=existing[3],
            expiry_date=datetime.fromisoformat(existing[4]) if existing[4] else None,
            updated_at=datetime.fromisoformat(existing[5]),
            category=existing[6]
        )
        
        # 更新データを適用
        update_data = ingredient_update.dict(exclude_unset=True)
        updated_ingredient = current_ingredient.copy(update=update_data)
        
        # 材料を更新
        updated_row = [
            ingredient_id,
            updated_ingredient.name,
            updated_ingredient.quantity,
            updated_ingredient.unit,
            updated_ingredient.expiry_date.isoformat() if updated_ingredient.expiry_date else "",
            datetime.now().isoformat(),
            updated_ingredient.category
        ]
        update_sheet(SPREADSHEET_ID, f"Ingredients!A{ingredient_id+1}", [updated_row])
        
        return updated_ingredient
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/ingredients/{ingredient_id}")
async def delete_ingredient(ingredient_id: int):
    """材料を削除"""
    try:
        # 既存の材料を確認
        values = read_sheet(SPREADSHEET_ID, f"Ingredients!A{ingredient_id+1}:A{ingredient_id+1}")
        if not values:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # 材料を削除
        delete_sheet(SPREADSHEET_ID, f"Ingredients!A{ingredient_id+1}:G{ingredient_id+1}")
        return {"message": "Ingredient deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# レシピ関連のエンドポイント
@router.get("/recipes", response_model=List[Recipe])
async def get_recipes():
    """レシピ一覧を取得"""
    try:
        values = read_sheet(SPREADSHEET_ID, "Recipes!A2:G")
        recipes = []
        for row in values:
            # 材料リストをJSONからパース
            ingredients = [RecipeIngredient(**ing) for ing in eval(row[2])]
            recipe = Recipe(
                id=int(row[0]),
                name=row[1],
                ingredients=ingredients,
                servings=int(row[3]),
                url=row[4],
                category=row[5],
                last_cooked=datetime.fromisoformat(row[6]) if row[6] else None
            )
            recipes.append(recipe)
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recipes", response_model=Recipe)
async def create_recipe(recipe: Recipe):
    """新しいレシピを追加"""
    try:
        # 既存のレシピを取得して新しいIDを生成
        values = read_sheet(SPREADSHEET_ID, "Recipes!A2:A")
        new_id = len(values) + 1
        
        # 新しいレシピを追加
        new_row = [
            new_id,
            recipe.name,
            str([ing.dict() for ing in recipe.ingredients]),
            recipe.servings,
            recipe.url or "",
            recipe.category,
            recipe.last_cooked.isoformat() if recipe.last_cooked else ""
        ]
        write_sheet(SPREADSHEET_ID, f"Recipes!A{new_id+1}", [new_row])
        
        recipe.id = new_id
        return recipe
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: int, recipe: Recipe):
    """レシピを更新"""
    try:
        # 既存のレシピを確認
        values = read_sheet(SPREADSHEET_ID, f"Recipes!A{recipe_id+1}:A{recipe_id+1}")
        if not values:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # レシピを更新
        updated_row = [
            recipe_id,
            recipe.name,
            str([ing.dict() for ing in recipe.ingredients]),
            recipe.servings,
            recipe.url or "",
            recipe.category,
            recipe.last_cooked.isoformat() if recipe.last_cooked else ""
        ]
        update_sheet(SPREADSHEET_ID, f"Recipes!A{recipe_id+1}", [updated_row])
        
        recipe.id = recipe_id
        return recipe
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int):
    """レシピを削除"""
    try:
        # 既存のレシピを確認
        values = read_sheet(SPREADSHEET_ID, f"Recipes!A{recipe_id+1}:A{recipe_id+1}")
        if not values:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # レシピを削除
        delete_sheet(SPREADSHEET_ID, f"Recipes!A{recipe_id+1}:G{recipe_id+1}")
        return {"message": "Recipe deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# レシピ検索API
@router.get("/recipes/search", response_model=List[Recipe])
async def search_recipes(
    ingredients: Optional[str] = None,
    category: Optional[str] = None,
    min_servings: Optional[int] = None
):
    """材料に基づいてレシピを検索"""
    try:
        # 全レシピを取得
        values = read_sheet(SPREADSHEET_ID, "Recipes!A2:G")
        recipes = []
        
        for row in values:
            # 材料リストをJSONからパース
            recipe_ingredients = [RecipeIngredient(**ing) for ing in eval(row[2])]
            recipe = Recipe(
                id=int(row[0]),
                name=row[1],
                ingredients=recipe_ingredients,
                servings=int(row[3]),
                url=row[4],
                category=row[5],
                last_cooked=datetime.fromisoformat(row[6]) if row[6] else None
            )
            
            # フィルタリング条件をチェック
            if ingredients:
                # 材料名でフィルタリング（部分一致）
                if not any(ing.lower() in recipe.name.lower() or 
                          any(ing.lower() in i.name.lower() for i in recipe.ingredients)
                          for ing in ingredients.split(',')):
                    continue
            
            if category and recipe.category.lower() != category.lower():
                continue
                
            if min_servings and recipe.servings < min_servings:
                continue
            
            recipes.append(recipe)
        
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 