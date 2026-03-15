import requests
import pandas as pd
import time
from datetime import datetime

# 目標設置
API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
FILE_NAME = "inventory_report.csv"
last_stock = None
data_log = []

def get_stock():
    try:
        # 添加 User-Agent 模擬真實瀏覽器訪問
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(API_URL, headers=headers, timeout=10)
        return response.json()['data']['stock']
    except Exception as e:
        print(f"[{datetime.now()}] 請求失敗: {e}")
        return None

print("監控已啟動，請確保網頁沒有關閉...")

while True:
    current_stock = get_stock()
    
    if current_stock is not None:
        if last_stock is not None and current_stock < last_stock:
            order_qty = last_stock - current_stock
            data_log.append({'時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '下單數量': order_qty})
            
            # 轉換為 DataFrame 進行處理
            df = pd.DataFrame(data_log)
            # 按下單數量降序排列
            df = df.sort_values(by='下單數量', ascending=False).reset_index(drop=True)
            
            # 標記排名邏輯
            df['排名'] = df.index + 1
            df['分組'] = '其他'
            df.loc[df['排名'] <= 25, '分組'] = '前25名'
            df.loc[(df['排名'] >= 26) & (df['排名'] <= 40), '分組'] = '26-40名'
            
            # 保存為 CSV (Excel 可直接打開)
            df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 監測到下單 {order_qty} 件，報告已更新。")
        
        last_stock = current_stock
    
    # 每 60 秒監測一次，確保頻率符合需求
    time.sleep(60)
