
from aixiaoliang_agent.tools.registry import default_registry
from aixiaoliang_agent.tools import stock_data # Register tools
from datetime import datetime, timedelta

def test_market_daily_cols():
    tools = {t.name: t for t in default_registry.get_tools()}
    get_market_daily = tools['get_market_daily'].func
    
    # Try a known trading day: last Friday 20251212
    trade_date = '20251212'
    print(f"Testing get_market_daily for {trade_date}...")
    
    res = get_market_daily(trade_date=trade_date)
    
    if res['status'] == 'success':
        data = res['data']
        print(f"Success! Found {len(data)} records.")
        if data:
            first_row = data[0]
            print("Columns:", first_row.keys())
            if 'up_limit' in first_row and 'down_limit' in first_row:
                print("VERIFIED: up_limit/down_limit present.")
            else:
                print("FAILED: up_limit/down_limit MISSING.")
    else:
        print(f"Status: {res['status']}, Meta: {res.get('meta')}, Error: {res.get('error')}")

if __name__ == "__main__":
    test_market_daily_cols()
