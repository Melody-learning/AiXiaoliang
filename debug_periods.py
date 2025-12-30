import os
import tushare as ts
import pandas as pd

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def debug_periods():
    print("🔎 Checking reporting periods for 688648.SH (Zhongyou Tech)...")
    try:
        # Fetch last 5 periods
        df = pro.fina_indicator(ts_code='688648.SH', limit=5, fields='ts_code,end_date,roe')
        print(df)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_periods()
