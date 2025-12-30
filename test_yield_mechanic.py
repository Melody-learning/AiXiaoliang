
import sys
import os
import time
from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data  # Ensure tools are registered
import aixiaoliang_agent.tools.knowledge_tool # Ensure knowledge tool is registered

def test_yield_behavior():
    print("Initializing Agent...")
    tools = default_registry.get_tools()
    # Use Flash for stability in testing
    agent = CodeAgent(model_name="gemini-2.0-flash-exp", tools=tools)

    # The query that caused "Three Loops" (Hallucinated Sequentiality)
    query = "筛选出市盈率小于10且股息率大于5%的股票"
    
    print(f"Running Query: {query}")
    print("-" * 50)
    
    step_count = 0
    
    # Run in full stream mode to capture all output
    try:
        for chunk in agent.run(query, stream_mode="full", log_subdir="tests"):
            print(f"[CHUNK] {chunk}")
            if "Running Code" in chunk or "running code" in chunk:
                step_count += 1
    except Exception as e:
        print(f"[ERROR IN RUN] {e}")
            
    print("\n" + "-" * 50)
    print("Test Complete.")

if __name__ == "__main__":
    test_yield_behavior()
