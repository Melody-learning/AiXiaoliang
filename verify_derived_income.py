import os
import tushare as ts
import pandas as pd

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def verify_derived_income():
    print("🔎 Verifying Derived Revenue/Profit Logic...")
    
    # 1. Fetch Daily Basic (MV, PE, PS) for 600519.SH (Moutai)
    # Tushare MV unit is Wan (10k). PE/PS are ratios.
    df_basic = pro.daily_basic(ts_code='600519.SH', trade_date='20251217', 
                               fields='ts_code,total_mv,pe_ttm,ps_ttm')
    
    if df_basic.empty:
        print("Error: No basic data.")
        return

    rec = df_basic.iloc[0]
    total_mv = rec['total_mv'] * 10000 # Convert Wan to Yuan
    pe_ttm = rec['pe_ttm']
    ps_ttm = rec['ps_ttm']
    
    print(f"\n[Basic Data]")
    print(f"Total MV: {total_mv:,.0f}")
    print(f"PE TTM: {pe_ttm}")
    print(f"PS TTM: {ps_ttm}")
    
    # Derive
    derived_rev = total_mv / ps_ttm if ps_ttm else 0
    derived_prof = total_mv / pe_ttm if pe_ttm else 0
    
    print(f"\n[Derived TTM]")
    print(f"Revenue TTM: {derived_rev:,.0f}")
    print(f"Profit TTM:  {derived_prof:,.0f}")
    
    # 2. Compare with Actual Income Data (Annual or recent 4Q sum)
    # Let's fetch actual Income Statement (Latest)
    # 600519 usually reports well.
    print(f"\n[Actual Data Comparison]")
    # Fetch typical revenue/profit from 2024 (Annual) or similar? 
    # Or just fetch latest income report.
    df_inc = pro.income(ts_code='600519.SH', period='20250930', fields='total_revenue,n_income_attr_p')
    if not df_inc.empty:
        act_rev = df_inc.iloc[0]['total_revenue']
        act_prof = df_inc.iloc[0]['n_income_attr_p']
        print(f"2025Q3 YTD Revenue: {act_rev:,.0f}")
        print(f"2025Q3 YTD Profit:  {act_prof:,.0f}")
        print("Note: TTM = Q3 YTD + (LastYear Annual - LastYear Q3 YTD). So mismatch is expected but magnitude should match.")
    else:
        print("No actual income data.")

if __name__ == "__main__":
    verify_derived_income()
