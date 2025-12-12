
import json
import re
from typing import List

def _sanitize_history(history: List[str]) -> List[str]:
    """
    Clean the history to remove HTML tags (like <details>) and Brain Traces.
    """
    clean_history = []
    for line in history:
        # Remove <details>...</details> blocks (Brain Trace)
        # Use DOTALL to match newlines inside tags
        cleaned = re.sub(r'<details>.*?</details>', '', line, flags=re.DOTALL)
        
        print(f"DEBUG SANITIZE:\nOrig Len: {len(line)}\nClean Len: {len(cleaned)}")
        # print(f"Content: {cleaned}")
        
        if cleaned.strip():
            clean_history.append(cleaned.strip())
    return clean_history

def test():
    log_path = "logs/trace_1765505903.json"
    print(f"Loading {log_path}...")
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Reconstruct the Assistant Message as it would appear in History
    # It mimics what 'full_buffer' would contain at end of run
    
    # Trace 903 steps: Thought -> Code -> Execution
    # Thought Step (Type: thought)
    step1_thought = data['steps'][0]['content']
    # Code Step is redundant in log (Step 2 is just code string)
    # Execution Trace (Type: execution_trace) contains the HTML block
    step3_exec = data['steps'][2]['content']
    
    # Reconstruct the "Brain Trace" wrapper for Thought
    thought_block = f"""
<details>
<summary>🧠 Brain Trace (Attempt 1)</summary>
{step1_thought}
</details>
"""
    
    # In run(), we yield: Thinking... -> Brain Trace -> Running code... -> Exec Trace
    full_msg = "Thinking about '平安银行现在的价格是多少？'... (Attempt 1)\n"
    full_msg += thought_block
    full_msg += "\nrunning code (Attempt 1)... 🏃\n"
    
    # Exec Trace in log (Step 3) ALREADY contains the HTML <details> for code validation?
    # Let's check the log content format:
    # "\n<details>\n<summary>💻 Code Execution...</details>...Result..."
    full_msg += step3_exec
    
    history_line = f"Assistant: {full_msg}"
    
    print("-" * 20)
    print("Reconstructed History Line (First 200 chars):")
    print(history_line[:200])
    print("-" * 20)
    
    # Sanitize
    cleaned_list = _sanitize_history([history_line])
    
    print("-" * 20)
    print("Cleaned Result:")
    if cleaned_list:
        print(cleaned_list[0])
    else:
        print("[EMPTY]")
        
    print("-" * 20)
    if "11.37" in str(cleaned_list):
        print("✅ SUCCESS: Result 11.37 preserved.")
    else:
        print("❌ FAILURE: Result lost.")

if __name__ == "__main__":
    test()
