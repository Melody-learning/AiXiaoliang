
import os
import sys
from dotenv import load_dotenv
from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.stock_data import (
    search_stock, get_current_price, get_fundamentals_data,
    get_industry_stocks, get_history_data, get_concepts,
    get_concept_stocks, get_market_daily, plot_price_history
)
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data # Trigger registration
import aixiaoliang_agent.tools.knowledge_tool # Trigger registration

# Load Env
load_dotenv()

def run_test(query: str, test_name: str):
    print(f"\n{'='*20} TEST: {test_name} {'='*20}")
    print(f"Query: {query}")
    
    # Get tools from registry
    tools = default_registry.get_tools()
    print(f"DEBUG: Loaded tools: {[t.name for t in tools]}")
    
    agent = CodeAgent(model_name="gemini-2.0-flash-exp", tools=tools)
    
    print("-" * 10 + " Execution Start " + "-" * 10)
    
    # Iterate over the generator to execute steps
    for output in agent.run(query, log_subdir="tests"):
        print(output, end="") # Print chunks as they come
    
    print("\n" + "-" * 10 + " Execution End " + "-" * 10)
    print("="*50)

if __name__ == "__main__":
    # Case 1: The "Latency Trap"
    # Logic: Agent asks for today -> Tool returns Empty+Hint -> Agent reads Hint -> Agent asks for Yesterday -> Success.
    run_test("帮我查找今天的涨停股（Market Daily）", "Latency Trap (Envelope Hint)")
    
    # Case 2: Basic envelope handling
    # Logic: Search Industry -> Success Envelope -> Extract Data
    run_test("列出所有的'白酒'概念股", "Basic Envelope Parsing")
