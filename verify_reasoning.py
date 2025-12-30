
import os
import sys
from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data
import aixiaoliang_agent.tools.knowledge_tool

def run_test():
    print(f"\n{'='*20} TEST: Agentic Reasoning (Limit Up) {'='*20}")
    # The query is specific: "1-limit-up stocks" (First Limit Up)
    query = "一连板的股票有哪些"
    print(f"Query: {query}")
    
    tools = default_registry.get_tools()
    
    agent = CodeAgent(model_name="gemini-2.0-flash-exp", tools=tools)
    
    print("-" * 10 + " Execution Start " + "-" * 10)
    
    output_log = ""
    for output in agent.run(query, log_subdir="tests"):
        print(output, end="")
        output_log += output
        
    print("\n" + "-" * 10 + " Execution End " + "-" * 10)
    
    # Validation Logic
    if "get_market_daily" in output_log and "pct_chg" in output_log:
        print("\n[+] SUCCESS: Agent used 'get_market_daily' and reasoning (pct_chg).")
    elif "get_limit_list" in output_log:
         print("\n[!] FAILURE: Agent tried to use removed tool 'get_limit_list'. Hallucination?")
    else:
         print("\n[?] WARNING: Review logs. Did not see expected tool usage.")

    print("="*50)

if __name__ == "__main__":
    run_test()
