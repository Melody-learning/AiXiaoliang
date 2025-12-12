from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import sys
import io

# Setup Agent
tools = default_registry.get_tools()
agent = CodeAgent(model_name="gemini-2.5-pro", tools=tools)

print(">>> Starting ReAct Capability Test <<<")

# Test 1: Intentional Error (Argument Hallucination)
# We ask it to search using a specific argument that might not exist or use English to encourage 'ticker' vs 'keyword' confusion.
# However, to be sure it fails first, we can try to influence it or just rely on its natural tendency.
# Let's try: "Search for stock with ticker symbol '600519'" 
# The tool 'search_stock' takes 'keyword'. 
# If agent tries search_stock(item='600519'), it will fail.
# But 2.5 Pro is smart. 
# Let's try a harder one: "Call search_stock with argument 'query' set to 'Moutai'."
# This FORCES the agent to make a mistake if it follows instructions blindly vs tool definition.
print("\n--- Test 1: Self-Correction (Forced Argument Error) ---")
query1 = "Call search_stock function with the argument 'query' set to '贵州茅台'. Do not use 'keyword' argument initially."
# We expect: 
# 1. Agent calls search_stock(query='贵州茅台') -> TypeError.
# 2. Agent catches error.
# 3. Agent reads signature: search_stock(keyword: str).
# 4. Agent calls search_stock(keyword='贵州茅台') -> Success.

history = []
for chunk in agent.run(query1, history=history, stream_mode="full"):
    pass # Consume generator
print("Test 1 Finished. Check logs.")

# Test 2: Memory (Context)
# We assume Test 1 found Moutai (600519.SH).
# Ask: "What is its current price?"
print("\n--- Test 2: Memory (Context Recall) ---")
# We fake the history to ensure independent test if Test 1 failed, 
# OR we pass the actual history if we want integration.
# Let's pass a constructed history to precise test Memory independent of Test 1 result.
fake_history = [
    "User: 帮我查一下平安银行的代码",
    "Assistant: 平安银行的代码是 000001.SZ"
]
query2 = "它的当前价格是多少？" 
# Expect: get_current_price('000001.SZ')
for chunk in agent.run(query2, history=fake_history, stream_mode="full"):
    pass
print("Test 2 Finished.")
