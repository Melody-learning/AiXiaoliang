from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry
import aixiaoliang_agent.tools.stock_data # Trigger registration

print(">>> Starting Real-World Context Test <<<")
tools = default_registry.get_tools()
agent = CodeAgent(model_name="gemini-2.5-pro", tools=tools)

# Step 1: Get Context
history = []
q1 = "帮我查一下平安银行的代码"
print(f"User: {q1}")
print("Agent generating response...")

# Capture usage of full stream mode as App uses
full_response_1 = ""
for chunk in agent.run(q1, history=history, stream_mode="full"):
    full_response_1 = chunk

print(f"Agent Response 1 (Length: {len(full_response_1)} chars)")
# print(full_response_1) # Validating debug

# Construct History object as App does
history = [f"User: {q1}", f"Assistant: {full_response_1}"]

# Step 2: Use Context
q2 = "它的当前价格是多少？"
print(f"\nUser: {q2}")
print("Agent thinking (with history)...")

full_response_2 = ""
for chunk in agent.run(q2, history=history, stream_mode="full"):
    full_response_2 = chunk

print("\n--- Final Answer for 'Its Price' ---")
# Check if answer contains prices
if "10." in full_response_2 or "Price" in full_response_2 or "价格" in full_response_2:
    print("SUCCESS: Price found.")
else:
    print("FAILURE: Agent did not find price. Check Trace.")

print(full_response_2)

# Step 3: PE Ratio (The Failure Case)
history.append(f"User: {q2}")
history.append(f"Assistant: {full_response_2}")

q3 = "它的PE呢"
print(f"\nUser: {q3}")
print("Agent thinking (with history)...")

full_response_3 = ""
for chunk in agent.run(q3, history=history, stream_mode="full"):
    full_response_3 = chunk

print("\n--- Final Answer for 'Its PE' ---")
if "None" not in full_response_3 and ("PE" in full_response_3 or "市盈率" in full_response_3):
    print("SUCCESS: PE ratio found!")
else:
    print("FAILURE: PE ratio is None or missing.")

print(full_response_3)
