import tushare as ts
import os
from dotenv import load_dotenv

load_dotenv()

# FORCE USE TUSHARE SPECIFIC PROXY as per User instruction
os.environ["HTTP_PROXY"] = "http://tushare.xyz:5000"
# Clear HTTPS just in case, or leave it? Tushare usually uses HTTP for this tunnel?
if "HTTPS_PROXY" in os.environ: del os.environ["HTTPS_PROXY"]

token = os.getenv("TUSHARE_TOKEN")
print(f"Testing Token: {token[:10]}...{token[-5:] if token else 'None'}")

if not token:
    print("[!] No token found in environment.")
    exit(1)

try:
    ts.set_token(token)
    pro = ts.pro_api()
    print("[*] Attempting to fetch trade calendar...")
    df = pro.trade_cal(exchange='', start_date='20240101', end_date='20240105')
    if not df.empty:
        print("[+] Token is VALID. Data fetched:")
        print(df.head(2))
    else:
        print("[!] Token valid but returned no data?")
except Exception as e:
    print(f"[!] Token Verification Failed: {e}")
