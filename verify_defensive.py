
import os
import sys
from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data

def run_test():
    print(f"\n{'='*20} TEST: Defensive Coding (Schema Check) {'='*20}")
    query = "好想你 current price. Inspect the structure carefully."
    print(f"Query: {query}")
    
    tools = default_registry.get_tools()
    
    # Increase temperature slightly to allow for creative thinking (or standard 0)
    agent = CodeAgent(model_name="gemini-2.0-flash-exp", tools=tools)
    
    print("-" * 10 + " Execution Start " + "-" * 10)
    
    steps_log = []
    
    for output in agent.run(query, log_subdir="tests"):
        print(output, end="")
        steps_log.append(output)

    print("\n" + "-" * 10 + " Execution End " + "-" * 10)
    
    full_log = "".join(steps_log)
    
    # Validation Logic
    # 1. Did it crash?
    if "string indices must be integers" in full_log or "object has no attribute" in full_log:
        print("\n[!] FAILURE: Agent crashed with Type Error. Defensive coding failed.")
    elif "print(res['data'])" in full_log or "print(res)" in full_log:
         print("\n[+] SUCCESS: Agent inspected the data structure.")
    elif "10.23 (Date:" in full_log:
         print("\n[+] SUCCESS: Agent printed the result (maybe implicitly knew, but didn't crash).")
    else:
         print("\n[?] WARNING: Review logs. Outcome unclear.")

    print("="*50)

if __name__ == "__main__":
    run_test()
