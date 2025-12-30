import os
import tushare as ts

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def debug_income_tiny():
    print("🔎 Debugging Tushare Income API (Tiny Batch)...")
    
    # Test Chunk (2 Stocks)
    print("\n[Test] Chunk (2 Stocks) for 20250930")
    codes = ['600519.SH', '000001.SZ']
    codes_str = ",".join(codes)
    try:
        df = pro.income(ts_code=codes_str, period='20250930', fields='ts_code,end_date,total_revenue,n_income_attr_p')
        print(f"Shape: {df.shape}")
        print(df)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_income_tiny()
