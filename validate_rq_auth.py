import rqdatac
import os
import time
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("RQ_LICENSE_KEY")

print(f"[*] Starting Aggressive Auth Validator for Key: {key[:10]}...")

MAX_ATTEMPTS = 50
for i in range(MAX_ATTEMPTS):
    try:
        rqdatac.init(username=key, password=key)
        print(f"\n[SUCCESS] Connected on attempt {i+1}!")
        print(f"Data Check: {rqdatac.current_snapshot('000001.XSHE').last}")
        break
    except Exception as e:
        print(f"\n[FAIL Attempt {i+1}] {e}")
        time.sleep(0.5)
else:
    print(f"\n[FAILURE] verification failed after {MAX_ATTEMPTS} attempts.")
