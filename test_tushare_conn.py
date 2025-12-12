import os
import tushare as ts
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TUSHARE_TOKEN")
print(f"Token loaded: {bool(token)}")

# Proxy as per user instruction
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"

try:
    pro = ts.pro_api(token)
    print("API Initialized. Fetching Index Basic...")
    df = pro.index_basic(limit=5, fields=["ts_code", "name", "market"])
    print("Success! Data preview:")
    print(df)
    
    print("\nFetching Stock Basic (Ping An)...")
    # Ping An Bank usually 000001.SZ
    df_stock = pro.stock_basic(ts_code='000001.SZ', fields='ts_code,symbol,name')
    print(df_stock)
    
except Exception as e:
    print(f"Failed: {e}")
