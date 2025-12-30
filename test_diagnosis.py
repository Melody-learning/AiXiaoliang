from aixiaoliang_agent.app import create_agent
import traceback

try:
    print("Creating Agent...")
    agent = create_agent()
    print("Agent created.")
    
    query = "1. 平安银行现在的滚动市盈率是多少？"
    print(f"Running query: {query}")
    
    steps = 0
    for chunk in agent.run(query, history=[], session_id="diagnosis_session"):
        print(f"CHUNK: {chunk}")
        steps += 1
        
    print(f"Finished. Total chunks: {steps}")

except Exception:
    traceback.print_exc()
