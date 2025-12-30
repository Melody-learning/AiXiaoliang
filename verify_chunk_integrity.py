import os
import tushare as ts

token = os.getenv("TUSHARE_TOKEN")
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
pro = ts.pro_api(token)

def verify_chunk_integrity():
    print("🔎 Replicating Chunk 5000 Integrity...")
    
    # 1. Get full list
    basics = pro.stock_basic(exchange='', list_status='L', fields='ts_code')
    all_codes = basics['ts_code'].tolist()
    
    # Find index of 688648.SH
    try:
        idx = all_codes.index('688648.SH')
        print(f"✅ Found 688648.SH at index {idx}")
    except ValueError:
        print("❌ 688648.SH not in list!")
        return

    # 2. Determine chunk boundary
    chunk_size = 50
    chunk_start = (idx // chunk_size) * chunk_size
    chunk = all_codes[chunk_start : chunk_start + chunk_size]
    
    print(f"Start Index: {chunk_start}, Chunk Size: {len(chunk)}")
    print(f"Target in Chunk? {'688648.SH' in chunk}")
    
    # 3. Execute
    codes_str = ",".join(chunk)
    period = '20250930'
    fields = 'ts_code,end_date,roe,roe_dt,gross_margin,netprofit_margin,dt_eps'
    
    print("Executing API call with this EXACT chunk...")
    df = pro.fina_indicator(ts_code=codes_str, period=period, fields=fields)
    
    # 4. Check result
    if '688648.SH' in df['ts_code'].values:
        print("✅ SUCCESS: 688648.SH returned in this chunk!")
        record = df[df['ts_code'] == '688648.SH'].iloc[0].to_dict()
        print(record)
    else:
        print("❌ FAILURE: 688648.SH dropped by Tushare API in this chunk.")
        print(f"Returned {len(df)} records for {len(chunk)} inputs.")

if __name__ == "__main__":
    verify_chunk_integrity()
