
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from aixiaoliang_agent.tools.stock_data import get_concepts, get_concept_stocks, get_market_daily

def test_market_tools():
    print("🚀 Starting Market Tools Verification...")
    
    # 1. Test get_concepts
    print("\n[1] Testing get_concepts(src='ts')...")
    concepts = get_concepts(src='ts')
    if isinstance(concepts, list) and len(concepts) > 0:
        print(f"✅ Success: Fetched {len(concepts)} concepts.")
        print(f"   Sample: {concepts[0]}")
        first_concept_id = concepts[0].get('code')
    else:
        print(f"❌ Failed: get_concepts returned {type(concepts)}: {concepts}")
        return

    # 2. Test get_concept_stocks
    if first_concept_id:
        print(f"\n[2] Testing get_concept_stocks(id='{first_concept_id}')...")
        stocks = get_concept_stocks(id=first_concept_id)
        if isinstance(stocks, list) and len(stocks) > 0:
            print(f"✅ Success: Fetched {len(stocks)} stocks for concept {first_concept_id}.")
            print(f"   Sample: {stocks[0]}")
        else:
            print(f"⚠️ Warning: Concept {first_concept_id} has {len(stocks) if isinstance(stocks, list) else 'invalid'} stocks. (Might be empty or failed)")
            # Try a known concept if possible, but let's proceed.

    # 3. Test get_market_daily
    # Use a recent date. Current time in prompt is 2025-12-16.
    # Let's try 2024-12-13 (a Friday, usually safe) or 2024-12-16 if data is real-time?
    # Actually, the user's previous logs showed data for '20251211' working.
    # Wait, the log showed '20250619', wait, the previous log execution traces showed:
    # "get_history_data('...','20251211', '20251216')"
    # So 2025-12-15 (Monday) seems like a good candidate if it was a trading day.
    target_date = "20251215" 
    print(f"\n[3] Testing get_market_daily(trade_date='{target_date}')...")
    
    daily_data = get_market_daily(trade_date=target_date)
    
    if isinstance(daily_data, list) and len(daily_data) > 1000:
        print(f"✅ Success: Fetched market snapshot with {len(daily_data)} records.")
        print(f"   Sample: {daily_data[0]}")
        
        # 3.1 Verify 'code' key exists (Normalization check)
        if 'code' in daily_data[0]:
             print("✅ Success: 'code' field present (Normalization working).")
        else:
             print("❌ Failure: 'code' field missing in market data.")
             
    else:
        print(f"❌ Failed (or holiday?): Fetched {len(daily_data) if isinstance(daily_data, list) else daily_data} records.")
        print("   If empty list, it might be a holiday or insufficient permissions/points.")

if __name__ == "__main__":
    test_market_tools()
