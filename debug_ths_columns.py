
import tushare as ts
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def debug_ths():
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        print("No TUSHARE_TOKEN found.")
        return
        
    pro = ts.pro_api(token)
    try:
        df = pro.ths_member(ts_code='883958.TI')
        print("Columns:", df.columns.tolist())
        if not df.empty:
            print("First row:", df.iloc[0].to_dict())
        else:
            print("Empty DataFrame returned.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_ths()
