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
        data = response.json()
        
        # 直接使用 skuList 進行加總，避免錯誤
        sku_list = data.get('skuList', [])
        current_total = sum(item.get('stocks', 0) for item in sku_list)
        
        return current_total
    except Exception as e:
        print(f"解析錯誤: {e}")
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
