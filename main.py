import os
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
REPORT_FILE = "inventory_report.csv"
LAST_STOCK_FILE = "last_inventory.csv" # 改成 CSV 格式以便儲存多個成員的數值

def get_current_stock():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://page.kmstation.net/'
        }
        response = requests.get(API_URL, headers=headers, timeout=15)
        data = response.json()
        
        # 提取成員庫存
        sku_list = data.get('skuList', [])
        current_stocks = {}
        for item in sku_list:
            # 簡化名稱，只取名字部分
            name = item.get('skuName', '未知').replace('【簽售】', '').strip()
            current_stocks[name] = item.get('stocks', 0)
            
        return current_stocks
    except Exception as e:
        print(f"解析錯誤: {e}")
        return None

def update_inventory():
    current_stocks = get_current_stock()
    if current_stocks is None: return

    # 讀取上次庫存 (使用 DataFrame 讀取)
    if os.path.exists(LAST_STOCK_FILE):
        last_stocks = pd.read_csv(LAST_STOCK_FILE).iloc[0].to_dict()
    else:
        last_stocks = {}

    # 檢查是否有變動
    has_changed = False
    details = []
    for name, qty in current_stocks.items():
        if last_stocks.get(name, 0) != qty:
            has_changed = True
            diff = last_stocks.get(name, 0) - qty
            details.append(f"{name}: {last_stocks.get(name, 0)} -> {qty} (變動: {diff})")

    if has_changed:
        # 記錄到總報告
        new_row = pd.DataFrame([{**{'時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, **current_stocks}])
        
        if os.path.exists(REPORT_FILE):
            df = pd.read_csv(REPORT_FILE)
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row
            
        df.to_csv(REPORT_FILE, index=False, encoding='utf-8-sig')
        
        # 更新基準檔
        pd.DataFrame([current_stocks]).to_csv(LAST_STOCK_FILE, index=False, encoding='utf-8-sig')
        print("庫存變動檢測:")
        for d in details: print(d)
    else:
        print("庫存無變化")

if __name__ == "__main__":
    update_inventory()
