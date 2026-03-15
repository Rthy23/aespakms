import os
import requests
import pandas as pd
from datetime import datetime

# 設定你要監測的商品列表
PRODUCTS = [
    {"id": "3973", "url": "https://kms.kmstation.net/prod/prodInfo?prodId=3973"},
    {"id": "3974", "url": "https://kms.kmstation.net/prod/prodInfo?prodId=3974"}
]

def get_current_stock(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://page.kmstation.net/'
        }
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        sku_list = data.get('skuList', [])
        current_stocks = {}
        for item in sku_list:
            name = item.get('skuName', '未知').replace('【簽售】', '').strip()
            current_stocks[name] = item.get('stocks', 0)
        return current_stocks
    except Exception as e:
        print(f"解析 {url} 時發生錯誤: {e}")
        return None

def update_inventory():
    for prod in PRODUCTS:
        prod_id = prod['id']
        url = prod['url']
        
        current_stocks = get_current_stock(url)
        if current_stocks is None: continue

        report_file = f"inventory_report_{prod_id}.csv"
        last_stock_file = f"last_inventory_{prod_id}.csv"

        # 讀取上次庫存
        if os.path.exists(last_stock_file):
            last_stocks = pd.read_csv(last_stock_file).iloc[0].to_dict()
        else:
            last_stocks = {}

        # 檢查變動
        has_changed = False
        details = []
        for name, qty in current_stocks.items():
            if last_stocks.get(name, 0) != qty:
                has_changed = True
                diff = last_stocks.get(name, 0) - qty
                details.append(f"商品 {prod_id} - {name}: {last_stocks.get(name, 0)} -> {qty} (變動: {diff})")

        if has_changed:
            new_row = pd.DataFrame([{**{'時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, **current_stocks}])
            
            if os.path.exists(report_file):
                df = pd.read_csv(report_file)
                df = pd.concat([df, new_row], ignore_index=True)
            else:
                df = new_row
            df.to_csv(report_file, index=False, encoding='utf-8-sig')
            pd.DataFrame([current_stocks]).to_csv(last_stock_file, index=False, encoding='utf-8-sig')
            
            print(f"商品 {prod_id} 變動檢測:")
            for d in details: print(d)
        else:
            print(f"商品 {prod_id} 庫存無變化")

if __name__ == "__main__":
    update_inventory()
