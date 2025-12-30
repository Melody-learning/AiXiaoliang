
import os
import sys
from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data
import aixiaoliang_agent.tools.knowledge_tool

def run_test():
    print(f"\n{'='*20} TEST: Termination Check {'='*20}")
    query = "好想你今天股价多少 涨跌幅"
    print(f"Query: {query}")
    
    tools = default_registry.get_tools()
    print(f"DEBUG: Loaded tools: {[t.name for t in tools]}")
    
    agent = CodeAgent(tools=tools)
    
    print("-" * 10 + " Execution Start " + "-" * 10)
    
    steps = 0
    for output in agent.run(query, log_subdir="tests"):
        print(output, end="")
        if "--- Step 10 ---" in output:
             print("\n[!] FAILURE: Still running at Step 10. Termination logic failed.")
             sys.exit(1)
        if "(Success in" in output or "(No code action." in output:
             print("\n[+] SUCCESS: Agent terminated correctly.")
             return

    print("\n" + "-" * 10 + " Execution End " + "-" * 10)
    print("="*50)

if __name__ == "__main__":
    run_test()
