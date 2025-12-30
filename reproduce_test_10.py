
import sys
import os

# Ensure the agent can be imported
sys.path.append(os.path.join(os.getcwd(), 'aixiaoliang_agent'))

from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry

# Must import modules to trigger registration
import aixiaoliang_agent.tools.stock_data
import aixiaoliang_agent.tools.knowledge_tool

def test_question_10():
    print("Initializing Agent...")
    tools = default_registry.get_tools()
    
    agent = CodeAgent(tools=tools, model_name='gemini-2.0-flash-exp')
    
    query = "10. 筛选出市盈率小于10且股息率大于5%的股票。"
    print(f"\n>>> Running Query: {query}")
    
    step_count = 0
    try:
        # Use stream_mode="full" to see intermediate steps
        for response in agent.run(query, stream_mode="full"):
            step_count += 1
            print(f"--- Step {step_count} ---")
            print(f"Content: {response[:200]}...") # Print first 200 chars
            
        print("\n>>> Finished.")
        print(f"Total Steps Yielded: {step_count}")
        
    except Exception as e:
        print(f"\n>>> Crashed: {e}")

if __name__ == "__main__":
    test_question_10()
