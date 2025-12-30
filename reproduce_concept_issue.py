
from aixiaoliang_agent.tools.registry import default_registry
from aixiaoliang_agent.tools import stock_data # Register tools

def test_concept_bug():
    tools = {t.name: t for t in default_registry.get_tools()}
    get_concept_stocks = tools['get_concept_stocks'].func
    
    # Test with a known THS concept ID from the logs: '883958.TI' (昨日连板)
    ths_id = '883958.TI'
    print(f"Testing get_concept_stocks with THS ID: {ths_id}")
    
    res = get_concept_stocks(id=ths_id)
    print(f"Result Status: {res['status']}")
    print(f"Result Data Len: {len(res['data']) if res['data'] else 0}")
    print(f"Result Meta: {res.get('meta')}")
    print(f"Result Error: {res.get('error')}")

if __name__ == "__main__":
    test_concept_bug()
