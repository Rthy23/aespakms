import os
import requests
import pandas as pd
from datetime import datetime

# 目標 API 與檔案
API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
FILE_NAME = "inventory_report.csv"

def get_current_stock():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://page.kmstation.net/'
        }
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        # --- 除錯核心 ---
        print(f"原始回傳內容 (RAW): {response.text}") 
        # ----------------
        
        data = response.json()
        
        # 根據你之前的觀察，如果資料是在 data 層級下：
        if 'data' in data:
            sku_list = data['data']['skuList']
            return sum(item['stocks'] for item in sku_list)
        else:
            print(f"警告: JSON 結構中找不到 'data' 鍵。現有結構: {data.keys()}")
            return None
            
    except Exception as e:
        print(f"API 請求錯誤: {e}")
        return None

def update_inventory():
    current_stock = get_current_stock()
    if current_stock is None:
        return

    # 1. 讀取或初始化數據
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        last_stock = df['當前庫存'].iloc[-1]
    else:
        df = pd.DataFrame(columns=['時間', '當前庫存', '下單數量', '排名', '分組'])
        last_stock = current_stock

    # 2. 檢測下單量
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

        # 3. 排序與標記
        orders = df[df['下單數量'] > 0].copy()
        orders = orders.sort_values(by='下單數量', ascending=False).reset_index(drop=True)
        orders['排名'] = orders.index + 1
        
        orders['分組'] = '其他'
        orders.loc[orders['排名'] <= 25, '分組'] = '前25名'
        orders.loc[(orders['排名'] >= 26) & (orders['排名'] <= 40), '分組'] = '26-40名'
        
        orders.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
        print(f"成功捕捉到下單，本次減少: {order_qty}，當前總庫存: {current_stock}")
    else:
        print(f"目前總庫存: {current_stock} (無變化)")

if __name__ == "__main__":
    update_inventory()
