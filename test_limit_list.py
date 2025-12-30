
import tushare as ts
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_limit_list():
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        print("No TUSHARE_TOKEN found.")
        return
        
    pro = ts.pro_api(token)
    
    # Try to get limit list for the most recent trading day
    # We'll try today, then yesterday, then Friday to be safe
    date_to_try = datetime.now().strftime('%Y%m%d')
    
    print(f"Testing limit_list for date: {date_to_try}")
    
    try:
        df = pro.limit_list(trade_date=date_to_try)
        if df.empty:
            print("Empty result for today. Trying yesterday...")
            date_to_try = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            df = pro.limit_list(trade_date=date_to_try)
            
        if df.empty:
            print("Still empty. Trying 2 days ago...")
            date_to_try = (datetime.now() - timedelta(days=2)).strftime('%Y%m%d')
            df = pro.limit_list(trade_date=date_to_try)

        print(f"Final Date Used: {date_to_try}")
        print("Columns:", df.columns.tolist())
        if not df.empty:
            print(f"Found {len(df)} records.")
            print("First row:", df.iloc[0].to_dict())
            
            # Check if we can filter for 1-limit-up (首板)
            # Usually 'limit' column or 'reason' might indicate it? 
            # Or we infer it from 'con_l_u' (consecutive limit up)?
            if 'l_b' in df.columns: # l_b = lián bǎn?
                 print("Found 'l_b' column!")
            if 'con_l_u' in df.columns: # consecutive limit up?
                 print("Found 'con_l_u' column!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_limit_list()
