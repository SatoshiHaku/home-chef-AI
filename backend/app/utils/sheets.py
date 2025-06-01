from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle

# スコープの設定（必要最小限の権限に制限）
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_service():
    """Google Sheets APIのサービスを取得する"""
    creds = None
    
    # トークンが存在する場合は読み込む
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # 有効な認証情報がない場合は新規取得
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # トークンを保存
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)

def initialize_sheets(spreadsheet_id: str):
    """スプレッドシートの初期化（ヘッダー行の設定）"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # スプレッドシートの情報を取得
        spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        # シートIDを取得
        sheet_ids = {}
        for s in sheets:
            sheet_ids[s['properties']['title']] = s['properties']['sheetId']
        
        # 材料シートのヘッダー
        ingredients_headers = [
            ['id', 'name', 'quantity', 'unit', 'expiry_date', 'updated_at', 'category']
        ]
        
        # レシピシートのヘッダー
        recipes_headers = [
            ['id', 'name', 'ingredients', 'servings', 'url', 'category', 'last_cooked']
        ]
        
        # ヘッダーの書き込み
        if 'Ingredients' in sheet_ids:
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range='Ingredients!A1',
                valueInputOption='RAW',
                body={'values': ingredients_headers}
            ).execute()
        
        if 'Recipes' in sheet_ids:
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range='Recipes!A1',
                valueInputOption='RAW',
                body={'values': recipes_headers}
            ).execute()
        
        # ヘッダー行の書式設定
        requests = []
        
        # Ingredientsシートの書式設定
        if 'Ingredients' in sheet_ids:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_ids['Ingredients'],
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.8,
                                'green': 0.8,
                                'blue': 0.8
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            })
        
        # Recipesシートの書式設定
        if 'Recipes' in sheet_ids:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_ids['Recipes'],
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.8,
                                'green': 0.8,
                                'blue': 0.8
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            })
        
        if requests:
            sheet.batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
        
        print("スプレッドシートの初期化が完了しました。")
    
    except Exception as e:
        print(f"スプレッドシートの初期化中にエラーが発生しました: {str(e)}")
        raise

def read_sheet(spreadsheet_id: str, range_name: str):
    """スプレッドシートからデータを読み取る"""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    return result.get('values', [])

def write_sheet(spreadsheet_id: str, range_name: str, values: list):
    """スプレッドシートにデータを書き込む"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # 既存のデータを取得
        existing_data = read_sheet(spreadsheet_id, range_name)
        
        # 新しいデータを追加
        if not existing_data:
            # ヘッダー行がない場合は追加
            if range_name.startswith('Ingredients'):
                existing_data = [['id', 'name', 'quantity', 'unit', 'expiry_date', 'updated_at', 'category']]
            elif range_name.startswith('Recipes'):
                existing_data = [['id', 'name', 'ingredients', 'servings', 'url', 'category', 'last_cooked']]
        
        # 新しいデータを追加
        existing_data.extend(values)
        
        # データを書き込む
        body = {
            'values': existing_data
        }
        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"データの書き込みが完了しました: {result}")
        return result
    
    except Exception as e:
        print(f"データの書き込み中にエラーが発生しました: {str(e)}")
        raise

def update_sheet(spreadsheet_id: str, range_name: str, values: list):
    """スプレッドシートのデータを更新する"""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    body = {
        'values': values
    }
    result = sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    return result

def delete_sheet(spreadsheet_id: str, range_name: str):
    """スプレッドシートのデータを削除する"""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    
    # 行を削除するリクエストを作成
    start_row = int(range_name.split('!')[1].split(':')[0][1:]) - 1  # 0-based index
    end_row = int(range_name.split('!')[1].split(':')[1][1:])  # 1-based index
    
    request = {
        'requests': [{
            'deleteDimension': {
                'range': {
                    'sheetId': 0,  # Ingredientsシート
                    'dimension': 'ROWS',
                    'startIndex': start_row,
                    'endIndex': end_row
                }
            }
        }]
    }
    
    # 行を削除
    result = sheet.batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request
    ).execute()
    
    return result 