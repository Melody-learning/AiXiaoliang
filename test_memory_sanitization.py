from aixiaoliang_agent.agent.code_agent import CodeAgent
from aixiaoliang_agent.tools.registry import default_registry

tools = default_registry.get_tools()
agent = CodeAgent(model_name="gemini-2.5-pro", tools=tools)

# Construct "Dirty" History (Simulating Gradio output with Brain Trace)
dirty_history = [
    "User: 帮我查一下平安银行的代码",
    """Assistant: <details>
<summary>🧠 Brain Trace (Attempt 1)</summary>
Thought: User wants Ping An Bank code.
</details>

<details>
<summary>💻 Code Execution</summary>
```python
print(search_stock(keyword='平安银行'))
```
</details>

### 🏁 Result
Ping An Bank code is 000001.SZ
"""
]

print(">>> Testing Memory Context Recall with Noisy History <<<")
print("Dirty History Sample (Last 100 chars):", dirty_history[1][-100:])

# The Query relies on resolving '它' (It) -> 'Ping An Bank'
query = "它的市盈率是多少？"

# Method 1: Check Sanitization logic directly
print("\n[Check 1] Verify Sanitization Logic:")
cleaned = agent._sanitize_history(dirty_history)
print("Cleaned History:\n", cleaned)
# verification: "Result" should be there, "<details>" should be gone.

# Method 2: Run Agent
print("\n[Check 2] Run Agent with Dirty History:")
# If sanitization works, Agent receives clean prompts and SHOULD understand context.
for chunk in agent.run(query, history=dirty_history, stream_mode="full"):
    if "Attempt 3" in chunk: # If it loops too much, break
        break

print("\nFinished.")
