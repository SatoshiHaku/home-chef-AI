from openai import OpenAI
import os
import json
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

# OpenAIクライアントの初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """あなたは料理のアシスタントです。ユーザーのメッセージを解析し、以下のアクションを実行できます。
必ずJSON形式で応答してください。

日付の指定方法：
- 明日: 現在の日付 + 1日
- 明後日: 現在の日付 + 2日
- 来週: 現在の日付 + 7日
- 具体的な日付: YYYY-MM-DD形式

アクション一覧：
1. 材料の追加（add_ingredient）
2. 材料の更新（update_ingredient）
3. 材料の削除（delete_ingredient）
4. レシピの検索（search_recipes）
5. 材料一覧の表示（list_ingredients）
6. レシピの追加（add_recipe）

メッセージの解析ルール：
- 「材料を教えて」「材料一覧を表示して」などのメッセージ → list_ingredientsアクション
- 「材料を追加して」「材料を買って」などのメッセージ → add_ingredientアクション
- 「材料を使った」「材料を消費した」などのメッセージ → update_ingredientアクション
- 「材料を削除して」「材料を消して」などのメッセージ → delete_ingredientアクション
- 「レシピを探して」「レシピを検索して」などのメッセージ → search_recipesアクション
- 「レシピを追加して」「レシピを保存して」などのメッセージ → add_recipeアクション

材料一覧を表示する場合は、以下の形式で返してください：
{
    "message": "現在の材料一覧です。",
    "action": {
        "type": "list_ingredients"
    }
}

材料を追加する場合は、以下の形式で返してください：
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

材料を更新する場合は、以下の形式で返してください：
{
    "message": "材料を更新しました。",
    "action": {
        "type": "update_ingredient",
        "data": {
            "name": "材料名",
            "quantity": 数量,
            "unit": "単位"
        }
    }
}

材料を削除する場合は、以下の形式で返してください：
{
    "message": "材料を削除しました。",
    "action": {
        "type": "delete_ingredient",
        "data": {
            "name": "材料名"
        }
    }
}

レシピを検索する場合は、以下の形式で返してください：
{
    "message": "レシピの検索結果です。",
    "action": {
        "type": "search_recipes",
        "data": {
            "query": "検索キーワード"
        }
    }
}

レシピを追加する場合は、以下の形式で返してください：
{
    "message": "レシピを追加しました。",
    "action": {
        "type": "add_recipe",
        "data": {
            "name": "レシピ名",
            "ingredients": [
                {
                    "name": "材料名1",
                    "quantity": 数量1,
                    "unit": "単位1"
                }
            ],
            "servings": 何人分,
            "url": "レシピのURL",
            "category": "カテゴリー"
        }
    }
}

アクションが必要ない場合は、actionフィールドを省略してください。
必ずJSON形式で応答してください。"""

def extract_recipe_info(url: str) -> Dict:
    """URLからレシピ情報を抽出する"""
    try:
        # User-Agentを設定してブロックを回避
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # URLからHTMLを取得
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # サイトごとの処理
        if "cookpad.com" in url:
            return extract_cookpad_recipe(soup, url)
        elif "kurashiru.com" in url:
            return extract_kurashiru_recipe(soup, url)
        elif "delishkitchen.tv" in url:
            return extract_delishkitchen_recipe(soup, url)
        else:
            return {
                "error": "未対応のレシピサイトです",
                "url": url
            }
    
    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }

def extract_kurashiru_recipe(soup: BeautifulSoup, url: str) -> Dict:
    """クラシルのレシピ情報を抽出"""
    # タイトルの抽出
    title = None
    h1_title = soup.find('h1')
    if h1_title:
        title = h1_title.text.strip().replace('レシピ・作り方', '').strip()
    
    if not title:
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].split('|')[0].strip()
    
    if not title and soup.title:
        title = soup.title.string.split('|')[0].strip()
    
    # 材料の抽出
    ingredients = []
    ingredient_elements = soup.select('.ingredient-list li')
    for element in ingredient_elements:
        name = element.select_one('.ingredient-name')
        amount = element.select_one('.ingredient-amount')
        if name and amount:
            ingredients.append({
                "name": name.text.strip(),
                "amount": amount.text.strip()
            })
    
    # 手順の抽出
    steps = []
    step_elements = soup.select('.step-list li')
    for i, element in enumerate(step_elements, 1):
        description = element.select_one('.step-description')
        if description:
            steps.append({
                "step": i,
                "description": description.text.strip()
            })
    
    return {
        "title": title,
        "url": url,
        "ingredients": ingredients,
        "steps": steps,
        "source": "kurashiru"
    }

def extract_cookpad_recipe(soup: BeautifulSoup, url: str) -> Dict:
    """クックパッドのレシピ情報を抽出"""
    # タイトルの抽出
    title = None
    h1_title = soup.find('h1', class_='recipe-title')
    if h1_title:
        title = h1_title.text.strip()
    
    if not title:
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].split('|')[0].strip()
    
    # 材料の抽出
    ingredients = []
    ingredient_elements = soup.select('.ingredient-list li')
    for element in ingredient_elements:
        name = element.select_one('.ingredient-name')
        amount = element.select_one('.ingredient-amount')
        if name and amount:
            ingredients.append({
                "name": name.text.strip(),
                "amount": amount.text.strip()
            })
    
    # 手順の抽出
    steps = []
    step_elements = soup.select('.step-list li')
    for i, element in enumerate(step_elements, 1):
        description = element.select_one('.step-description')
        if description:
            steps.append({
                "step": i,
                "description": description.text.strip()
            })
    
    return {
        "title": title,
        "url": url,
        "ingredients": ingredients,
        "steps": steps,
        "source": "cookpad"
    }

def extract_delishkitchen_recipe(soup: BeautifulSoup, url: str) -> Dict:
    """デリッシュキッチンのレシピ情報を抽出"""
    # タイトルの抽出
    title = None
    h1_title = soup.find('h1', class_='recipe-title')
    if h1_title:
        title = h1_title.text.strip()
    
    if not title:
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].split('|')[0].strip()
    
    # 材料の抽出
    ingredients = []
    ingredient_elements = soup.select('.ingredient-list li')
    for element in ingredient_elements:
        name = element.select_one('.ingredient-name')
        amount = element.select_one('.ingredient-amount')
        if name and amount:
            ingredients.append({
                "name": name.text.strip(),
                "amount": amount.text.strip()
            })
    
    # 手順の抽出
    steps = []
    step_elements = soup.select('.step-list li')
    for i, element in enumerate(step_elements, 1):
        description = element.select_one('.step-description')
        if description:
            steps.append({
                "step": i,
                "description": description.text.strip()
            })
    
    return {
        "title": title,
        "url": url,
        "ingredients": ingredients,
        "steps": steps,
        "source": "delishkitchen"
    }

def get_llm_response(messages: list) -> dict:
    """LLMからの応答を取得する"""
    try:
        # 最後のメッセージがURLを含むかチェック
        last_message = messages[-1]["content"]
        if "http" in last_message:
            # URLを抽出
            url = last_message.split("http")[1].split()[0]
            url = "http" + url
            
            # レシピ情報を抽出
            recipe_info = extract_recipe_info(url)
            
            if "error" in recipe_info:
                return {
                    "action": "error",
                    "message": recipe_info["error"]
                }
            
            return {
                "action": "add_recipe",
                "recipe": recipe_info
            }
        
        # URLが含まれていない場合は通常のLLM処理
        # システムプロンプトを追加
        messages_with_system = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages
        ]
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages_with_system,
            temperature=0.7,
            max_tokens=1000
        )
        
        # レスポンスをJSONとしてパース
        try:
            response_data = json.loads(response.choices[0].message.content)
            return response_data
        except json.JSONDecodeError:
            # JSONとしてパースできない場合は通常のチャット応答として扱う
            return {
                "message": response.choices[0].message.content
            }
    
    except Exception as e:
        return {
            "action": "error",
            "message": str(e)
        } 