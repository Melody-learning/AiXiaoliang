
from aixiaoliang_agent.tools.registry import default_registry
from aixiaoliang_agent.tools import stock_data # Register tools
from datetime import datetime, timedelta

def test_limit_tool():
    tools = {t.name: t for t in default_registry.get_tools()}
    get_limit_list = tools['get_limit_list'].func
    
    # Try today, if empty try yesterday (tool might return empty for today if market open but limit list not generated, or closed)
    # We will just try a known recent trading day logic or let the tool handle it?
    # The tool takes YYYYMMDD.
    # Let's try 3 days ago to be safe (likely a trading day has passed)
    
    # Actually let's try a few recent dates until we get data
    for days_back in range(0, 5):
        date_str = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
        print(f"Testing get_limit_list for {date_str}...")
        res = get_limit_list(trade_date=date_str)
        
        if res['status'] == 'success':
            print(f"Success! Found {len(res['data'])} records.")
            print("First record keys:", res['data'][0].keys())
            print("First record values:", res['data'][0])
            break
        else:
            print(f"Status: {res['status']}, Meta: {res.get('meta')}, Error: {res.get('error')}")

if __name__ == "__main__":
    test_limit_tool()
