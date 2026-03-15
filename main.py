import os
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
REPORT_FILE = "inventory_report.csv"
LAST_STOCK_FILE = "last_inventory.txt"

def get_current_stock():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://page.kmstation.net/'
        }
        response = requests.get(API_URL, headers=headers, timeout=15)
        data = response.json()
        
        # 加總所有 SKU 的庫存
        sku_list = data.get('skuList', [])
        current_total = sum(item.get('stocks', 0) for item in sku_list)
        
        return current_total
    except Exception as e:
        print(f"解析錯誤: {e}")
        return None

def update_inventory():
    current_stock = get_current_stock()
    if current_stock is None: 
        return

    # 讀取上次庫存
    last_stock = None
    if os.path.exists(LAST_STOCK_FILE):
        with open(LAST_STOCK_FILE, 'r') as f:
            try:
                last_stock = int(f.read().strip())
            except ValueError:
                last_stock = None

    # 若為第一次執行，建立檔案並寫入初始值
    if last_stock is None:
        with open(LAST_STOCK_FILE, 'w') as f:
            f.write(str(current_stock))
        
        initial_df = pd.DataFrame([{
            '時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '當前庫存': current_stock,
            '變動數量': 0
        }])
        initial_df.to_csv(REPORT_FILE, index=False, encoding='utf-8-sig')
        print(f"初始化基準庫存: {current_stock}，檔案已建立。")
    
    # 若庫存有變化，更新報告與基準檔
    elif current_stock != last_stock:
        order_qty = last_stock - current_stock
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
        with open(LAST_STOCK_FILE, 'w') as f:
            f.write(str(current_stock))
        print(f"庫存變動: {last_stock} -> {current_stock} (變動: {order_qty})")
    
    else:
        print(f"庫存無變化: {current_stock}")

if __name__ == "__main__":
    update_inventory()
