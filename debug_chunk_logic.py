import os
import tushare as ts

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def debug_chunk_logic():
    print("🔎 Debugging Chunk Logic for 688648.SH...")
    
    # 1. Check if stock is in stock_basic
    basics = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name')
    target = basics[basics['ts_code'] == '688648.SH']
    
    if target.empty:
        print("❌ Critical: 688648.SH NOT found in stock_basic list!")
        return
    else:
        print(f"✅ Found in stock_basic: {target.iloc[0].to_dict()}")
        
    # 2. Simulate the chunk query
    # Create a small chunk including this stock and some others
    chunk_codes = ['600519.SH', '000001.SZ', '688648.SH', '601318.SH']
    codes_str = ",".join(chunk_codes)
    period = '20250930'
    fields = 'ts_code,end_date,roe,roe_dt,gross_margin,netprofit_margin,dt_eps'
    
    print(f"\nSimulating Chunk Query for: {codes_str}")
    try:
        df = pro.fina_indicator(ts_code=codes_str, period=period, fields=fields)
        print("Result:")
        print(df)
        
        if '688648.SH' in df['ts_code'].values:
            print("✅ 688648.SH returned in chunk query.")
        else:
            print("❌ 688648.SH MISSING from chunk query result!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_chunk_logic()
