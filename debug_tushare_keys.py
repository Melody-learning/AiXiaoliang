
import tushare as ts
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

print("[*] Fetching daily_basic for 000001.SZ...")
df = pro.daily_basic(ts_code='000001.SZ', limit=1, fields='ts_code,trade_date,pe,pe_ttm,pb,total_mv,dv_ratio,dv_ttm')
print("Columns:", df.columns.tolist())
print("Values:\n", df.head(1).T)

print("\n[*] Fetching without fields limit...")
df_full = pro.daily_basic(ts_code='000001.SZ', limit=1)
print("Columns (Full):", df_full.columns.tolist())
if 'pe_ttm' in df_full.columns:
    print("pe_ttm value:", df_full.iloc[0]['pe_ttm'])
else:
    print("pe_ttm NOT FOUND in full columns.")
