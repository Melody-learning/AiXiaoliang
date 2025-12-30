import sys
import os
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta

# Ensure project root in path
sys.path.append(os.getcwd())
# Note: get_income_statement removed.
from aixiaoliang_agent.tools.stock_data import get_daily_basic, get_financial_indicator, get_concepts, get_concept_stocks

def verify_challenges():
    print("🚀 Running Final System Verification (5 Challenge Questions)...")
    
    # Pre-fetch Data
    # 1. Daily Basic (Valuation + Revenue/Profit TTM) for 20251217
    print("\n[Data Fetch] Getting Valuation+Growth Data (20251217)...")
    res_basic = get_daily_basic('20251217')
    if res_basic['status'] != 'success': 
        print(f"❌ Failed Basic: {res_basic.get('error')}")
        return
    df_basic = pd.DataFrame(res_basic['data'])
    print(f"   Shape: {df_basic.shape}")
    print(f"   Columns: {list(df_basic.columns)}")

    # 2. Financials (ROE/Margins) for 20250930
    print("\n[Data Fetch] Getting Financials (20250930)...")
    res_fin = get_financial_indicator('20250930')
    if res_fin['status'] != 'success': 
        print(f"❌ Failed Financials: {res_fin.get('error')}")
        return
    df_fin = pd.DataFrame(res_fin['data'])
    print(f"   Shape: {df_fin.shape}")

    # No separate Income Fetch needed anymore!

    # --- Challenge 1: PE < 15 & ROE > 20% ---
    print("\n------------------------------------------------")
    print("1. 🎯 [Value+Profit] PE(TTM) < 15 & ROE > 20%")
    merged_1 = pd.merge(df_basic, df_fin, on='ts_code', suffixes=('', '_fin'))
    merged_1['pe_ttm'] = pd.to_numeric(merged_1['pe_ttm'], errors='coerce')
    merged_1['roe'] = pd.to_numeric(merged_1['roe'], errors='coerce')
    
    res_1 = merged_1[
        (merged_1['pe_ttm'] < 15) & 
        (merged_1['pe_ttm'] > 0) & 
        (merged_1['roe'] > 20)
    ]
    print(f"   ✅ Count: {len(res_1)}")
    if len(res_1) > 0: print(res_1[['ts_code', 'pe_ttm', 'roe']].head(3).to_string(index=False))

    # --- Challenge 2: Div > 5% & Net Margin > 15% ---
    print("\n------------------------------------------------")
    print("2. 💰 [Yield+Margin] Div Yield > 5% & Net Margin > 15%")
    # Already merged in merged_1
    merged_2 = merged_1.copy()
    merged_2['dv_ratio'] = pd.to_numeric(merged_2['dv_ratio'], errors='coerce')
    merged_2['netprofit_margin'] = pd.to_numeric(merged_2['netprofit_margin'], errors='coerce')
    
    res_2 = merged_2[
        (merged_2['dv_ratio'] > 5) & 
        (merged_2['netprofit_margin'] > 15)
    ]
    print(f"   ✅ Count: {len(res_2)}")
    if len(res_2) > 0: print(res_2[['ts_code', 'dv_ratio', 'netprofit_margin']].head(3).to_string(index=False))

    # --- Challenge 3: Mkt Cap < 50亿 & Revenue > 20亿 ---
    print("\n------------------------------------------------")
    print("3. 🚀 [Small Cap+Growth] Total MV < 50亿 & Revenue(TTM) > 20亿")
    # Revenue is now in df_basic as 'total_revenue_ttm' (Unit: Yuan)
    # Total MV in df_basic is 10k (Wan). BUT wait, normalize_stock_records usually keeps it.
    # In my get_daily_basic logic, I didn't change total_mv in place, I just used it to calc revenue.
    # So total_mv is still in Wan.
    
    merged_3 = df_basic.copy()
    merged_3['total_mv'] = pd.to_numeric(merged_3['total_mv'], errors='coerce') # Wan
    merged_3['total_revenue_ttm'] = pd.to_numeric(merged_3['total_revenue_ttm'], errors='coerce') # Yuan
    
    # 50 Billion = 50 * 100,000,000 ??? No, 50 Yi.
    # 50 Yi = 5,000,000,000 Yuan.
    # MV (Wan) < 5,000,000,000 / 10,000 = 500,000 Wan.
    
    # Revenue > 20 Yi = 2,000,000,000 Yuan.
    
    res_3 = merged_3[
        (merged_3['total_mv'] < 500000) & 
        (merged_3['total_revenue_ttm'] > 2000000000)
    ]
    print(f"   ✅ Count: {len(res_3)}")
    if len(res_3) > 0: print(res_3[['ts_code', 'total_mv', 'total_revenue_ttm']].head(3).to_string(index=False))

    # --- Challenge 4: 'Semiconductor' & Gross Margin > 40% ---
    print("\n------------------------------------------------")
    print("4. 💎 [Sector+Margin] 'Semiconductor' & Gross Margin > 40%")
    # Need to fetch sector
    from aixiaoliang_agent.tools.stock_data import get_industry_stocks
    
    res_ind = get_industry_stocks('半导体')
    if res_ind['status'] == 'success':
        semi_stocks = [x['ts_code'] for x in res_ind['data']]
        print(f"   Found {len(semi_stocks)} semiconductor stocks.")
        
        # Filter df_fin
        res_4 = df_fin[
            (df_fin['ts_code'].isin(semi_stocks)) & 
            (pd.to_numeric(df_fin['gross_margin'], errors='coerce') > 40)
        ]
        print(f"   ✅ Count: {len(res_4)}")
        if len(res_4) > 0: print(res_4[['ts_code', 'gross_margin']].head(3).to_string(index=False))
    else:
        print("   ❌ Failed to find Semiconductor sector.")

    # --- Challenge 5: Revenue > 1000亿 & PE < 10 ---
    print("\n------------------------------------------------")
    print("5. 🏢 [Blue Chip] Revenue(TTM) > 1000亿 & PE < 10")
    
    merged_5 = df_basic.copy()
    
    # Revenue > 1000 Yi = 100,000,000,000
    res_5 = merged_5[
        (pd.to_numeric(merged_5['total_revenue_ttm'], errors='coerce') > 100000000000) & 
        (pd.to_numeric(merged_5['pe_ttm'], errors='coerce') < 10) &
        (pd.to_numeric(merged_5['pe_ttm'], errors='coerce') > 0)
    ]
    print(f"   ✅ Count: {len(res_5)}")
    if len(res_5) > 0: print(res_5[['ts_code', 'pe_ttm', 'total_revenue_ttm']].head(3).to_string(index=False))

if __name__ == "__main__":
    verify_challenges()
