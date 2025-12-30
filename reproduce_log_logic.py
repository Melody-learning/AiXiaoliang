import sys
import os
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.getcwd())
from aixiaoliang_agent.tools.stock_data import get_daily_basic, get_financial_indicator

def reproduce_log():
    print("🔎 Reproducing Agent Logic from Session 1766039943...")
    
    # Simulate Agent's Date Selection
    today = datetime.now() # Roughly 2025-12-18
    trade_date = '20251217' # Hardcoded based on log success
    period = '20250930'     # Hardcoded based on log success
    
    # 1. Fetch PE
    print(f"Fetching PE for {trade_date}...")
    res_pe = get_daily_basic(trade_date=trade_date)
    pe_data = pd.DataFrame(res_pe['data'])
    
    # 2. Fetch ROE
    print(f"Fetching ROE for {period}...")
    res_roe = get_financial_indicator(period=period)
    roe_data = pd.DataFrame(res_roe['data'])
    
    # 3. Merge
    merged_df = pd.merge(pe_data, roe_data, on='ts_code')
    print(f"Merged Shape: {merged_df.shape}")
    
    # --- DEBUG SECTION ---
    target = '688648.SH'
    print(f"\n[DEBUG] Inspecting {target} in Merged Data:")
    row = merged_df[merged_df['ts_code'] == target]
    
    if row.empty:
        print("❌ Stock NOT FOUND in merged dataframe!")
        # Check source
        in_pe = target in pe_data['ts_code'].values
        in_roe = target in roe_data['ts_code'].values
        print(f"   In PE Data? {in_pe}")
        print(f"   In ROE Data? {in_roe}")
    else:
        print("✅ Stock FOUND in merged dataframe.")
        rec = row.iloc[0]
        pe_val = rec['pe_ttm']
        roe_val = rec['roe']
        print(f"   Values: PE_TTM={pe_val}, ROE={roe_val}")
        print(f"   Types:  PE_TTM={type(pe_val)}, ROE={type(roe_val)}")
        
        # Check Filter Logic
        cond_pe = pe_val < 15
        cond_pos = pe_val > 0
        cond_roe = roe_val > 20
        
        print("\n   [Filter Check]")
        print(f"   PE < 15? {cond_pe}")
        print(f"   PE > 0?  {cond_pos}")
        print(f"   ROE > 20? {cond_roe}")
        
    # --- END DEBUG ---

    # 4. Agent's Exact Filter
    filtered_stocks = merged_df[
        (merged_df['pe_ttm'] < 15) &
        (merged_df['pe_ttm'] > 0) & 
        (merged_df['roe'] > 20)
    ]
    
    print(f"\nFinal Result Count: {len(filtered_stocks)}")
    if target in filtered_stocks['ts_code'].values:
        print(f"✅ {target} IS in result.")
    else:
        print(f"❌ {target} IS NOT in result.")

if __name__ == "__main__":
    reproduce_log()
