import os
import tushare as ts
import random
import time

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def analyze_drop_rate():
    print("🔎 Analyzing Systematic Data Drop in 100-size Chunks...")
    
    # 1. Get full list
    basics = pro.stock_basic(exchange='', list_status='L', fields='ts_code')
    all_codes = basics['ts_code'].tolist()
    total_stocks = len(all_codes)
    print(f"Total Stocks: {total_stocks}")
    
    chunk_size = 100
    fields = 'ts_code,end_date,roe'
    period = '20250930'
    
    drops = 0
    samples = 10 # Check 10 chunks (1000 stocks)
    
    print(f"Sampling {samples} chunks ({samples*100} stocks)...")
    
    for i in range(samples):
        # Pick random start
        start = random.randint(0, (total_stocks // chunk_size) - 1) * chunk_size
        chunk = all_codes[start : start + chunk_size]
        codes_str = ",".join(chunk)
        
        try:
            df = pro.fina_indicator(ts_code=codes_str, period=period, fields=fields)
            
            # Count unique returned codes
            returned_codes = df['ts_code'].unique() if not df.empty else []
            count = len(returned_codes)
            
            # Check for duplicates in response (which mask drops if total count is 100)
            total_rows = len(df)
            
            missing = set(chunk) - set(returned_codes)
            missing_count = len(missing)
            
            if missing_count > 0:
                print(f"[Chunk {start}] Sent: 100 | Returns: {total_rows} | Unique: {count} | ❌ Missing: {missing_count}")
                drops += missing_count
            else:
                 print(f"[Chunk {start}] Sent: 100 | Returns: {total_rows} | Unique: {count} | ✅ Clean")
                 
            time.sleep(0.5) # Politeness
            
        except Exception as e:
            print(f"[Chunk {start}] Error: {e}")

    print("-" * 30)
    print(f"Total Missing in Sample: {drops}")
    estimated_total_missing = (drops / (samples * 100)) * total_stocks
    print(f"📉 Estimated Total Missing Market-Wide: ~{int(estimated_total_missing)} stocks")
    
    if estimated_total_missing > 10:
        print("🚨 CONCLUSION: Widespread systematic data loss confirmed.")
    else:
        print("❓ CONCLUSION: Drops seem isolated.")

if __name__ == "__main__":
    analyze_drop_rate()
