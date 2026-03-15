import os
import requests
import pandas as pd
from datetime import datetime

# 設置目標 API 和檔案名稱
API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
FILE_NAME = "inventory_report.csv"

def get_current_stock():
    """從 API 獲取當前庫存"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(API_URL, headers=headers, timeout=15)
        # 請根據實際 API 返回的 JSON 結構調整這裡的鍵值
        return response.json()['data']['stock']
    except Exception as e:
        print(f"API 請求錯誤: {e}")
        return None

def update_inventory():
    current_stock = get_current_stock()
    if current_stock is None:
        return

    # 1. 讀取現有記錄
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        # 獲取上一次檢測到的庫存（假設最後一行是最近的）
        last_stock = df['當前庫存'].iloc[-1]
    else:
        df = pd.DataFrame(columns=['時間', '當前庫存', '下單數量', '排名', '分組'])
        last_stock = current_stock  # 初始化

    # 2. 檢測是否有下單（庫存減少）
    if current_stock < last_stock:
        order_qty = last_stock - current_stock
        new_row = {
            '時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '當前庫存': current_stock,
            '下單數量': order_qty,
            '排名': 0,
            '分組': ''
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # 3. 重新計算排序與分組
        # 僅對產生下單的記錄進行排序
        orders = df[df['下單數量'] > 0].copy()
        orders = orders.sort_values(by='下單數量', ascending=False).reset_index(drop=True)
        orders['排名'] = orders.index + 1
        
        # 標記分組
        orders['分組'] = '其他'
        orders.loc[orders['排名'] <= 25, '分組'] = '前25名'
        orders.loc[(orders['排名'] >= 26) & (orders['排名'] <= 40), '分組'] = '26-40名'
        
        # 保存更新
        orders.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
        print(f"檢測到下單: {order_qty}，報告已更新至 {FILE_NAME}")
    else:
        # 如果庫存沒變或增加，依然保存當前庫存狀態
        print(f"庫存未減少，當前庫存: {current_stock}")

if __name__ == "__main__":
    update_inventory()
