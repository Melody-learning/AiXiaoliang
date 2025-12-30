import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.getcwd())

from aixiaoliang_agent.tools.stock_data import get_daily_basic, get_financial_indicator
from datetime import datetime, timedelta

def debug_specific_stock():
    print("🔎 Investigating '688648.SH' (Zhongyou Tech)...")
    code = '688648.SH'
    
    # 1. Check PE (get_daily_basic)
    # Use recent trading date from previous logs: 20251217
    date_str = '20251217'
    print(f"\n[1] Checking PE for {date_str}...")
    res = get_daily_basic(date_str)
    
    pe_found = False
    if res['status'] == 'success':
        # Manually find the stock in list
        for item in res['data']:
            if item['ts_code'] == code:
                print(f"   ✅ Found Record: {item}")
                print(f"   👉 PE(TTM): {item.get('pe_ttm')}")
                pe_found = True
                break
    
    if not pe_found:
        print(f"   ❌ Record for {code} NOT found in daily basic data.")

    # 2. Check ROE (get_financial_indicator)
    # Use period 20250930
    period = '20250930'
    print(f"\n[2] Checking ROE for Period {period}...")
    res = get_financial_indicator(period)
    
    roe_found = False
    if res['status'] == 'success':
         for item in res['data']:
            if item['ts_code'] == code:
                print(f"   ✅ Found Record: {item}")
                print(f"   👉 ROE: {item.get('roe')}")
                roe_found = True
                break
    
    if not roe_found:
        print(f"   ❌ Record for {code} NOT found in financial data.")

if __name__ == "__main__":
    debug_specific_stock()
