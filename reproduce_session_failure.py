import sys
import os
import pandas as pd
import tushare as ts

# Ensure project root in path
sys.path.append(os.getcwd())
from aixiaoliang_agent.tools.stock_data import get_daily_basic, get_financial_indicator

def reproduce_failure():
    print("🔎 Reproducing Session Failure Logic...")
    
    # 1. Fetch PE (20251217) - Same as log
    print("\n[1] Fetching PE (20251217)...")
    pe_res = get_daily_basic('20251217')
    if pe_res['status'] != 'success':
        print("Failed to fetch PE.")
        return
    df_pe = pd.DataFrame(pe_res['data'])
    print(f"   Fetched {len(df_pe)} PE records.")

    # 2. Simulate Bad Date (20240331) - Same as log
    print("\n[2] Fetching ROE (20240331) - The Agent's Choice...")
    roe_res_bad = get_financial_indicator('20240331')
    
    if roe_res_bad['status'] == 'success':
        df_roe_bad = pd.DataFrame(roe_res_bad['data'])
        print(f"   Fetched {len(df_roe_bad)} ROE records.")
        
        # Merge & Filter
        merged_bad = pd.merge(df_pe, df_roe_bad, on='ts_code')
        results_bad = merged_bad[
            (merged_bad['pe_ttm'] < 15) & 
            (merged_bad['pe_ttm'] > 0) & 
            (merged_bad['roe'] > 20)
        ]
        print(f"   👉 Matches found with 20240331: {len(results_bad)}")
        if len(results_bad) > 0:
            print(results_bad[['ts_code', 'pe_ttm', 'roe']].head())
    else:
        print("   Failed to fetch ROE for 20240331.")

    # 3. Simulate Good Date (20250930) - Correct Choice
    print("\n[3] Fetching ROE (20250930) - Correct Choice...")
    roe_res_good = get_financial_indicator('20250930')
    
    if roe_res_good['status'] == 'success':
        df_roe_good = pd.DataFrame(roe_res_good['data'])
        print(f"   Fetched {len(df_roe_good)} ROE records.")
        
        # Merge & Filter
        merged_good = pd.merge(df_pe, df_roe_good, on='ts_code')
        results_good = merged_good[
            (merged_good['pe_ttm'] < 15) & 
            (merged_good['pe_ttm'] > 0) & 
            (merged_good['roe'] > 20)
        ]
        print(f"   👉 Matches found with 20250930: {len(results_good)}")
        if len(results_good) > 0:
            print(results_good[['ts_code', 'pe_ttm', 'roe']].head())
    else:
        print("   Failed to fetch ROE for 20250930.")

if __name__ == "__main__":
    reproduce_failure()
