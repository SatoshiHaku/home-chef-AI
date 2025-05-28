from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class IngredientBase(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    expiry_date: Optional[datetime] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(IngredientBase):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None

class Ingredient(IngredientBase):
    id: Optional[int] = None
    updated_at: datetime = datetime.now()

    class Config:
        from_attributes = True

class RecipeIngredient(BaseModel):
    name: str
    quantity: float
    unit: str

class Recipe(BaseModel):
    id: Optional[int] = None
    name: str
    ingredients: List[RecipeIngredient]
    servings: int
    url: Optional[str] = None
    category: str
    last_cooked: Optional[datetime] = None 