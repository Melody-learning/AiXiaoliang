import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data  # Import to register tools

def main():
    print(">>> AiXiaoliang 2.0 Agent Starting...")
    
    # Initialize Agent with registered tools
    tools = default_registry.get_tools()
    model_name = os.getenv("MODEL_NAME", "gemini-3-pro-preview")
    agent = CodeAgent(model_name=model_name, tools=tools)
    
    print(f"[*] Loaded {len(tools)} tools: {[t.name for t in tools]}")
    
    # Simple Interaction Loop
    print("\n>>> Ready! Type 'exit' to quit.")
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            if not user_input.strip():
                continue
                
            for output in agent.run(user_input):
                print(output)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()
