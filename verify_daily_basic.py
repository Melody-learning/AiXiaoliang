import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.getcwd())

from aixiaoliang_agent.tools.stock_data import get_daily_basic
from datetime import datetime, timedelta

def verify_daily_basic():
    print("🚀 Verifying `get_daily_basic` Tool...")
    
    # Try to find a valid trading day (last 5 days)
    today = datetime.now()
    data = None
    used_date = ""

    for i in range(5):
        date_to_try = today - timedelta(days=i)
        date_str = date_to_try.strftime('%Y%m%d')
        print(f"[*] Trying to fetch data for {date_str}...")
        
        res = get_daily_basic(trade_date=date_str)
        if res['status'] == 'success' and res['data']:
            data = res['data']
            used_date = date_str
            print(f"✅ Success! Fetched {len(data)} records for {date_str}.")
            break
        elif res['status'] == 'empty':
            print(f"[-] No data for {date_str} (likely holiday).")
        else:
            print(f"[!] Error for {date_str}: {res.get('error')}")

    if not data:
        print("❌ Failed to fetch data for any of the last 5 days.")
        return

    # Check for critical fields
    sample = data[0]
    required_fields = ['ts_code', 'pe', 'pe_ttm', 'pb', 'dv_ratio', 'total_mv']
    
    print("\n🔍 Inspecting Sample Record:")
    print(sample)
    
    missing_fields = [f for f in required_fields if f not in sample]
    
    if missing_fields:
        print(f"❌ Verification Failed! Missing fields: {missing_fields}")
    else:
        print("\n✅ Verification Passed! All required fundamental fields are present.")
        print(f"   - PE: {sample.get('pe')}")
        print(f"   - PE(TTM): {sample.get('pe_ttm')}")
        print(f"   - Dividend Yield: {sample.get('dv_ratio')}")

if __name__ == "__main__":
    verify_daily_basic()
