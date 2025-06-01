import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional
import os

def analyze_html_structure(url: str) -> Dict:
    """URLのHTML構造を解析し、重要な要素を抽出する"""
    try:
        # User-Agentを設定してブロックを回避
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # URLからHTMLを取得
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 基本的な情報を抽出
        result = {
            "url": url,
            "title": soup.title.string if soup.title else "No title found",
            "meta_description": soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else "No description found",
            "h1_tags": [h1.text.strip() for h1 in soup.find_all('h1')],
            "h2_tags": [h2.text.strip() for h2 in soup.find_all('h2')],
            "recipe_elements": {}
        }
        
        # クックパッドの場合
        if "cookpad.com" in url:
            result["recipe_elements"]["cookpad"] = {
                "title": extract_cookpad_title(soup),
                "ingredients": extract_cookpad_ingredients(soup),
                "steps": extract_cookpad_steps(soup)
            }
        
        # クラシルの場合
        elif "kurashiru.com" in url:
            title = extract_kurashiru_title(soup)
            result["recipe_elements"]["kurashiru"] = {
                "title": title,
                "ingredients": extract_kurashiru_ingredients(soup),
                "steps": extract_kurashiru_steps(soup)
            }
            # タイトルが見つかった場合、結果のタイトルも更新
            if title:
                result["title"] = title
        
        # デリッシュキッチンの場合
        elif "delishkitchen.tv" in url:
            result["recipe_elements"]["delishkitchen"] = {
                "title": extract_delishkitchen_title(soup),
                "ingredients": extract_delishkitchen_ingredients(soup),
                "steps": extract_delishkitchen_steps(soup)
            }
        
        # HTMLの構造を保存
        result["html_structure"] = {
            "head": str(soup.head)[:1000] if soup.head else "No head found",
            "body_start": str(soup.body)[:1000] if soup.body else "No body found"
        }
        
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }

def extract_cookpad_title(soup: BeautifulSoup) -> Optional[str]:
    """クックパッドのレシピタイトルを抽出"""
    # 複数の可能性のあるセレクタを試す
    selectors = [
        'h1.recipe-title',
        'h1.recipe-title__name',
        'h1.title',
        'h1[class*="title"]',
        'h1[class*="recipe"]'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            return element.text.strip()
    
    return None

def extract_cookpad_ingredients(soup: BeautifulSoup) -> List[Dict]:
    """クックパッドの材料を抽出"""
    ingredients = []
    # 複数の可能性のあるセレクタを試す
    selectors = [
        '.ingredient-list',
        '.ingredients',
        '[class*="ingredient"]',
        '[class*="material"]'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for element in elements:
                # 材料のテキストを取得
                text = element.text.strip()
                if text:
                    ingredients.append({"text": text, "selector": selector})
    
    return ingredients

def extract_cookpad_steps(soup: BeautifulSoup) -> List[str]:
    """クックパッドの手順を抽出"""
    steps = []
    # 複数の可能性のあるセレクタを試す
    selectors = [
        '.step',
        '.step-box',
        '[class*="step"]',
        '[class*="procedure"]'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for element in elements:
                text = element.text.strip()
                if text:
                    steps.append(text)
    
    return steps

def extract_kurashiru_title(soup: BeautifulSoup) -> Optional[str]:
    """クラシルのレシピタイトルを抽出"""
    # まずh1タグから試す
    h1_title = soup.find('h1')
    if h1_title:
        # 「レシピ・作り方」などの余分な文字を削除
        title = h1_title.text.strip()
        title = title.replace('レシピ・作り方', '').strip()
        if title:
            return title
    
    # メタデータから試す
    meta_title = soup.find('meta', property='og:title')
    if meta_title and meta_title.get('content'):
        title = meta_title['content']
        # 「| クラシル」などの余分な文字を削除
        title = title.split('|')[0].strip()
        return title
    
    # 通常のtitleタグから試す
    if soup.title:
        title = soup.title.string
        if title:
            # 「| クラシル」などの余分な文字を削除
            title = title.split('|')[0].strip()
            return title
    
    return None

def extract_kurashiru_ingredients(soup: BeautifulSoup) -> List[Dict]:
    """クラシルの材料を抽出"""
    ingredients = []
    # 材料リストの要素を取得
    ingredient_elements = soup.select('.ingredient-list li')
    
    for element in ingredient_elements:
        # 材料名と量を取得
        name = element.select_one('.ingredient-name')
        amount = element.select_one('.ingredient-amount')
        
        if name and amount:
            ingredients.append({
                "name": name.text.strip(),
                "amount": amount.text.strip()
            })
    
    return ingredients

def extract_kurashiru_steps(soup: BeautifulSoup) -> List[Dict]:
    """クラシルの手順を抽出"""
    steps = []
    # 手順リストの要素を取得
    step_elements = soup.select('.step-list li')
    
    for i, element in enumerate(step_elements, 1):
        # 手順の説明を取得
        description = element.select_one('.step-description')
        if description:
            steps.append({
                "step": i,
                "description": description.text.strip()
            })
    
    return steps

def extract_delishkitchen_title(soup: BeautifulSoup) -> Optional[str]:
    """デリッシュキッチンのレシピタイトルを抽出"""
    selectors = [
        'h1.recipe-title',
        'h1.title',
        'h1[class*="title"]',
        'h1[class*="recipe"]'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            return element.text.strip()
    
    return None

def extract_delishkitchen_ingredients(soup: BeautifulSoup) -> List[Dict]:
    """デリッシュキッチンの材料を抽出"""
    ingredients = []
    selectors = [
        '.ingredient-list',
        '.ingredients',
        '[class*="ingredient"]',
        '[class*="material"]'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for element in elements:
                text = element.text.strip()
                if text:
                    ingredients.append({"text": text, "selector": selector})
    
    return ingredients

def extract_delishkitchen_steps(soup: BeautifulSoup) -> List[str]:
    """デリッシュキッチンの手順を抽出"""
    steps = []
    selectors = [
        '.step',
        '.step-box',
        '[class*="step"]',
        '[class*="procedure"]'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for element in elements:
                text = element.text.strip()
                if text:
                    steps.append(text)
    
    return steps

def save_analysis_result(result: Dict, filename: str = "html_analysis.json"):
    """解析結果をJSONファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # テスト用のURL
    test_url = input("レシピのURLを入力してください: ")
    
    # HTML構造を解析
    result = analyze_html_structure(test_url)
    
    # 結果を保存
    save_analysis_result(result)
    
    # 結果を表示
    print("\n解析結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2)) 