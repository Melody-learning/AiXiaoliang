
from aixiaoliang_agent.tools.stock_data import get_fundamentals_data

def test_keys():
    print("Testing get_fundamentals_data('000001.SZ')...")
    res = get_fundamentals_data('000001.SZ')
    if isinstance(res, str): # Error message
        print(f"Tool Error: {res}")
        return

    print(f"Keys returned: {list(res.keys())}")
    
    # Assertions
    assert 'pe' in res, "Missing lowercase 'pe'"
    assert 'PE' in res, "Missing uppercase 'PE'"
    assert res['pe'] == res['PE'], "Values do not match!"
    
    print("✅ Logic Check Passed: 'PE' key exists and matches 'pe'.")

if __name__ == "__main__":
    test_keys()
