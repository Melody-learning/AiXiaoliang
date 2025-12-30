import os
import tushare as ts

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def debug_chunk():
    print("--- Debugging Chunk Query ---")
    codes = "600519.SH,000001.SZ,000002.SZ"
    period = "20250930"
    
    try:
        print(f"Querying fina_indicator for {codes}...")
        df = pro.fina_indicator(ts_code=codes, period=period, fields='ts_code,roe')
        print("Result:")
        print(df if not df.empty else "Empty")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_chunk()
