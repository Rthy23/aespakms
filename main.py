import requests
import pandas as pd
import time

API_URL = "https://kms.kmstation.net/prod/prodInfo?prodId=3973"
data_log = []
last_stock = None

def get_current_stock():
    # 這裡建議加上 headers 模擬瀏覽器，防止被封
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(API_URL, headers=headers)
        # 根據實際 JSON 路徑修改，通常是 data.stock 或類似鍵值
        return r.json().get('data', {}).get('stock', 0)
    except:
        return None

while True:
    current_stock = get_current_stock()
    
    if last_stock is not None and current_stock < last_stock:
        order_qty = last_stock - current_stock
        data_log.append({'time': pd.Timestamp.now(), 'order': order_qty})
        
        # 排序
        df = pd.DataFrame(data_log).sort_values(by='order', ascending=False)
        
        # 標記
        df['rank'] = range(1, len(df) + 1)
        df['group'] = '其他'
        df.loc[df['rank'] <= 25, 'group'] = '前25名'
        df.loc[(df['rank'] >= 26) & (df['rank'] <= 40), 'group'] = '26-40名'
        
        # 保存到 Excel
        df.to_csv('orders_report.csv', index=False)
        print(f"檢測到下單: {order_qty} 件。文件已更新。")

    last_stock = current_stock
    time.sleep(45) # 設定為 45 秒，避開太頻繁的請求
