import os
import tushare as ts
import pandas as pd

# Setup
token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def debug_financials():
    print("--- Debugging pro.fina_indicator ---")
    # Try getting ONE stock's history to see valid periods
    try:
        df = pro.fina_indicator(ts_code='600519.SH', limit=5)
        print("1. Single Stock (600519.SH) fetched:")
        print(df[['ts_code', 'end_date', 'roe']].head() if not df.empty else "Empty")
        
        if not df.empty:
            valid_period = df.iloc[0]['end_date']
            print(f"   Using valid period from above: {valid_period} to query all stocks...")
            
            # Try query all stocks with that period
            df_all = pro.fina_indicator(period=valid_period, limit=10)
            print(f"2. All Stocks for {valid_period}:")
            print(df_all.head() if not df_all.empty else "Empty")
            
            if df_all.empty:
               print("   Possible Cause: 'period' param not supported for batch query in this permission group?")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Debugging pro.income ---")
    try:
        df = pro.income(ts_code='600519.SH', limit=5, fields='ts_code,end_date,total_revenue')
        print("3. Single Stock (600519.SH) Income:")
        print(df.head() if not df.empty else "Empty")
        
        if not df.empty:
            valid_period = df.iloc[0]['end_date']
            print(f"   Using period {valid_period} for batch query...")
            df_all = pro.income(period=valid_period, limit=10, fields='ts_code,total_revenue')
            print(f"4. All Stocks Income for {valid_period}:")
            print(df_all.head() if not df_all.empty else "Empty")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_financials()
