import os
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
FILE_NAME = "inventory_report.csv"

def get_current_stock():
    try:
        # 加入瀏覽器 User-Agent 與來源 Referer
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://page.kmstation.net/'
        }
        response = requests.get(API_URL, headers=headers, timeout=15)
        # 印出 API 回傳內容以便除錯
        print(f"API 回傳內容: {response.text}")
        
        data = response.json()
        # 若 API 結構是 data['data']['stock']，這裡會成功
        return data['data']['stock']
    except Exception as e:
        print(f"API 請求錯誤: {e}")
        return None

def update_inventory():
    current_stock = get_current_stock()
    if current_stock is None:
        return

    # 讀取舊數據或建立新 DataFrame
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        last_stock = df['當前庫存'].iloc[-1]
    else:
        df = pd.DataFrame(columns=['時間', '當前庫存', '下單數量', '排名', '分組'])
        last_stock = current_stock

    # 若庫存減少，計算下單數量並記錄
    if current_stock < last_stock:
        order_qty = last_stock - current_stock
        new_entry = {
            '時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '當前庫存': current_stock,
            '下單數量': order_qty,
            '排名': 0,
            '分組': ''
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

        # 排序與分組
        orders = df[df['下單數量'] > 0].copy()
        orders = orders.sort_values(by='下單數量', ascending=False).reset_index(drop=True)
        orders['排名'] = orders.index + 1
        orders['分組'] = '其他'
        orders.loc[orders['排名'] <= 25, '分組'] = '前25名'
        orders.loc[(orders['排名'] >= 26) & (orders['排名'] <= 40), '分組'] = '26-40名'
        
        orders.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
        print(f"成功記錄: 下單 {order_qty} 件")
    else:
        print("庫存無變化")

if __name__ == "__main__":
    update_inventory()
