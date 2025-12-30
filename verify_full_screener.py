import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.getcwd())

from aixiaoliang_agent.tools.stock_data import get_daily_basic, get_financial_indicator, get_income_statement
from datetime import datetime, timedelta

def verify_full_screener():
    print("🚀 Verifying FULL BATCH SCREENER Suite...")
    
    # 1. Verify get_daily_basic (Valuation)
    print("\n[1/3] Testing Valuation Tool (get_daily_basic)...")
    # Try a recent trading day
    today = datetime.now()
    basic_success = False
    for i in range(5):
        date_to_try = (today - timedelta(days=i)).strftime('%Y%m%d')
        print(f"   Trying {date_to_try}...")
        res = get_daily_basic(date_to_try)
        if res['status'] == 'success' and res['data']:
            print(f"   ✅ Success! Fetched {len(res['data'])} records.")
            sample = res['data'][0]
            print(f"   🔍 Sample: PE={sample.get('pe_ttm')}, Dividend={sample.get('dv_ratio')}")
            basic_success = True
            break
            
    if not basic_success:
        print("   ❌ Failed to fetch daily basic data.")

    # 2. Verify get_financial_indicator (Profitability)
    print("\n[2/3] Testing Profitability Tool (get_financial_indicator)...")
    # Use a known quarter end (e.g., 20240930 or 20240630 depending on current date)
    # Since current date is Dec 2025 (based on logs), let's try 20240930 and 20250930 just in case.
    # Wait, the logs show "2025-12-18". So 20250930 should be available.
    periods = ['20250930', '20241231', '20240930'] 
    fin_success = False
    for p in periods:
        print(f"   Trying period {p}...")
        res = get_financial_indicator(p)
        if res['status'] == 'success' and res['data']:
            print(f"   ✅ Success! Fetched {len(res['data'])} records.")
            sample = res['data'][0]
            print(f"   🔍 Sample: ROE={sample.get('roe')}, GrossMargin={sample.get('gross_margin')}")
            fin_success = True
            break
            
    if not fin_success:
        print("   ❌ Failed to fetch financial indicators.")

    # 3. Verify get_income_statement (Growth)
    print("\n[3/3] Testing Growth Tool (get_income_statement)...")
    inc_success = False
    for p in periods:
        print(f"   Trying period {p}...")
        res = get_income_statement(p)
        if res['status'] == 'success' and res['data']:
            print(f"   ✅ Success! Fetched {len(res['data'])} records.")
            sample = res['data'][0]
            print(f"   🔍 Sample: Revenue={sample.get('total_revenue')}, NetProfit={sample.get('n_income_attr_p')}")
            inc_success = True
            break
            
    if not inc_success:
        print("   ❌ Failed to fetch income statement.")

    print("\n---------------------------------------------------")
    if basic_success and fin_success and inc_success:
        print("🎉 ALL SYSTEMS GO: The Full Batch Screener Suite is operational!")
    else:
        print("⚠️ SYSTEM PARTIALLY OPERATIONAL: Check failures above.")

if __name__ == "__main__":
    verify_full_screener()
