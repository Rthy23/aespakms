import os
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
REPORT_FILE = "inventory_report.csv"
LAST_STOCK_FILE = "last_inventory.txt" # 專門儲存上次庫存的檔案

def get_current_stock():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://page.kmstation.net/'
        }
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        # 這是最關鍵的一步：將回傳的內容強制印出來
        print(f"狀態碼: {response.status_code}")
        print(f"原始回應內容: {response.text}")
        
        data = response.json()
        
        # 如果能成功解析，我們再看看它的鍵值有哪些
        print(f"JSON 的頂層鍵值: {list(data.keys())}")
        
        if 'data' in data:
            sku_list = data['data']['skuList']
            return sum(item['stocks'] for item in sku_list)
        else:
            return None
            
    except Exception as e:
        print(f"API 請求錯誤: {str(e)}")
        return None

def update_inventory():
    current_stock = get_current_stock()
    if current_stock is None: return

    # 1. 讀取上次庫存
    if os.path.exists(LAST_STOCK_FILE):
        with open(LAST_STOCK_FILE, 'r') as f:
            last_stock = int(f.read().strip())
    else:
        # 第一次運行，將當前庫存設為基準，不記錄下單
        with open(LAST_STOCK_FILE, 'w') as f:
            f.write(str(current_stock))
        print(f"初始化基準庫存: {current_stock}")
        return

    # 2. 比較差異
    if current_stock != last_stock:
        order_qty = last_stock - current_stock
        # 記錄變動
        new_row = pd.DataFrame([{
            '時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '當前庫存': current_stock,
            '變動數量': order_qty
        }])
        
        if os.path.exists(REPORT_FILE):
            df = pd.read_csv(REPORT_FILE)
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row
            
        df.to_csv(REPORT_FILE, index=False, encoding='utf-8-sig')
        # 更新基準檔
        with open(LAST_STOCK_FILE, 'w') as f:
            f.write(str(current_stock))
        print(f"庫存變動: {last_stock} -> {current_stock} (變動: {order_qty})")
    else:
        print(f"庫存無變化: {current_stock}")

if __name__ == "__main__":
    update_inventory()
