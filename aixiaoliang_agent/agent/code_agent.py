import os
import re
import time
import json
import io
import sys
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure GenAI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Proxy Setup
if os.getenv("HTTP_PROXY"):
    os.environ["http_proxy"] = os.getenv("HTTP_PROXY")
    os.environ["https_proxy"] = os.getenv("HTTPS_PROXY")

# --- Memory Structures (ReAct) ---
class Step:
    def to_string(self):
        raise NotImplementedError

class TaskStep(Step):
    def __init__(self, task: str):
        self.task = task
    def to_string(self):
        return f"User Task: {self.task}"

class ThoughtStep(Step):
    def __init__(self, thought: str):
        self.thought = thought
    def to_string(self):
        return f"Thought: {self.thought}"

class CodeStep(Step):
    def __init__(self, code: str):
        self.code = code
    def to_string(self):
        return f"Code:\n```python\n{self.code}\n```"

class ObservationStep(Step):
    def __init__(self, output: str):
        self.output = output
    def to_string(self):
        return f"Observation:\n{self.output}"

class ErrorStep(Step):
    def __init__(self, error: str):
        self.error = error
    def to_string(self):
        return f"Execution Error:\n{self.error}\n[Tip: Use a different tool or arguments to fix the code.]"


class CodeAgent:
    def __init__(self, model_name: str = "gemini-2.0-pro-exp-02-05", tools: List[Any] = []):
        self.model_name = model_name
        self.tools = {tool.name: tool for tool in tools}
        print(f"DEBUG: Loaded tools: {list(self.tools.keys())}")
        self.memory: List[Step] = []
        self.max_steps = 3  # Allow up to 3 attempts (Self-Correction)

    def _build_system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in self.tools.items():
            import inspect
            sig = inspect.signature(tool.func)
            tool_descriptions.append(f"- {name}{sig}: {tool.description}")
        
        tool_desc_str = "\n".join(tool_descriptions)
        
        return f"""You are a helpful assistant that can write Python code to answer questions.

### Available Tools
You have access to the following global functions. Please use these exact names:

{tool_desc_str}

### Instructions
1. Answer the user's question by writing a Python code block (starts with ```python).
2. **Use only the tools listed above.** Do not invent new function names (e.g. 'stock_price' does not exist).
3. Use print() to output the answer.
4. Pay attention to argument names in the signatures.

### Error Handling & Reflection
- If your code fails with a `NameError` (e.g. 'stock_price' not defined), it means you used a wrong name.
- **Action**: Check the "Available Tools" list above to find the correct name (e.g. `get_current_price`), then write the corrected code.
"""

    def _sanitize_history(self, history: List[str]) -> List[str]:
        """
        Clean the history to remove HTML tags, Brain Traces, and intermediate status messages.
        Keeps only the User's query and the Agent's Final Result.
        """
        clean_history = []
        for line in history:
            print(f"DEBUG SANITIZE INPUT: {repr(line[:100])} (Len: {len(line)})")
            # 1. Remove <details>...</details> blocks (Brain Trace & Code Logs)
            cleaned = re.sub(r'<details>.*?</details>', '', line, flags=re.DOTALL)
            
            # 2. Split by newlines to process individual lines
            parts = cleaned.split('\n')
            filtered_parts = []
            
            for part in parts:
                part = part.strip()
                if not part: continue
                
                # Filter out "Thinking..." and "running code..." noise
                if part.startswith("Thinking about") or part.startswith("running code") or part.startswith("User:"):
                     # Keep "User:" lines, discard others
                    if part.startswith("User:"):
                        filtered_parts.append(part)
                    continue
                
                # Keep "Assistant:" prefix if it has content
                if part.startswith("Assistant:"):
                    # If the line is just "Assistant:", append it (next lines might be content)
                    # Or check if content follows.
                    # Usually "Assistant: Thinking..." is one line? No, typically separate.
                    # But in app.py: f"Assistant: {bot_msg}" -> bot_msg starts with "Thinking..."
                    # So "Assistant: Thinking..." should be removed?
                    # Better: Remove the "Thinking..." prefix if present.
                    if "Thinking about" in part:
                         # Remove "Thinking..." from the line
                         part = re.sub(r'Thinking about.*?(\(Attempt \d+\))?', '', part).strip()
                         # If "Assistant:" remains empty, skip?
                         if part == "Assistant:": continue
                    
                    filtered_parts.append(part)
                    continue

                # Keep Results and other text
                filtered_parts.append(part)
            
            final_line = "\n".join(filtered_parts).strip()
            
            # DEBUG: Log what's happening
            # print(f"DEBUG SANITIZE:\nOrig Len: {len(line)}\nClean Len: {len(final_line)}\nContent: {final_line[:100]}...")
            
            if final_line:
                clean_history.append(final_line)

        return clean_history

    def _build_prompt_from_memory(self, history: List[str] = None) -> str:
        system = self._build_system_prompt()
        
        # Add Conversation History (Memory)
        context_str = ""
        if history:
            # Sanitize history to prevent "Thought Pollution"
            clean_history = self._sanitize_history(history)
            context_str = "\n\nConversation History:\n" + "\n".join(clean_history)
            
        print(f"DEBUG: Final Context passed to LLM:\n{repr(context_str)}")
            
        # Add Current Steps (ReAct Trace)
        steps_str = "\n\n".join([step.to_string() for step in self.memory if not isinstance(step, TaskStep)])
        
        # Current Task is always the first Step for this run
        current_task = self.memory[0].task if self.memory else "No Task"
        
        return f"{system}{context_str}\n\nCurrent Task: {current_task}\n\nExisting Steps:\n{steps_str}\n\nYour Next Step (Write Python Code):"


    def run(self, user_input: str, history: List[str] = [], stream_mode: str = "delta", session_id: str = None):
        full_buffer = ""
        
        def yield_content(chunk, replace=False):
            nonlocal full_buffer
            if replace:
                full_buffer = chunk
            else:
                full_buffer += chunk
            return full_buffer if stream_mode == "full" else chunk

        # Reset Memory for this run (but keep 'history' passed from outside)
        self.memory = [TaskStep(user_input)]
        
        # Session Logging Setup
        if not session_id:
            session_id = f"session_{int(time.time())}"
            
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f"{session_id}.jsonl")
        
        # Prepare Log Entry for THIS turn
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": user_input,
            "steps": []
        }
        
        # Append initial entry to file (Start of Turn)
        # We will update this entry or append steps? 
        # Better: Append a specialized "Turn Start" line, then append steps as they happen?
        # User requested "One Log File" for the session.
        # Simplest valid JSONL: Each line is a complete Turn Object.
        # But we want to log *steps* as they happen?
        # Writing the whole Turn Object at the END is safer for valid JSONL.
            
        start_time = time.time()
        
        # ReAct Loop
        step_count = 0
        final_success = False
        
        yield yield_content(f"Thinking about '{user_input}'... (Attempt 1)\n")

        while step_count < self.max_steps:
            try:
                prompt = self._build_prompt_from_memory(history)
                
                # Call LLM
                llm_start = time.time()
                model = genai.GenerativeModel(self.model_name)
                # Safety settings omitted for brevity/compatibility (add back if needed)
                response = model.generate_content(prompt)
                llm_latency = time.time() - llm_start
                
                if not response.parts:
                    err = "[!] Empty Response from Model."
                    print(f"DEBUG: Empty Response. Prompt Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Unknown'}")
                    yield yield_content(f"{err}\n")
                    break # Stop if model broken
                    
                content = response.text
                self.memory.append(ThoughtStep(content))
                
                # Log Thought
                log_entry["steps"].append({"type": "thought", "content": content, "latency": llm_latency, "attempt": step_count+1})
                
                # Display Thought
                attempt_label = f"Attempt {step_count+1}"
                thought_block = f"""
<details>
<summary>🧠 Brain Trace ({attempt_label})</summary>
{content}
</details>
"""
                yield yield_content(thought_block)
                
                # Extract Code
                code_match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
                
                if code_match:
                    code = code_match.group(1)
                    self.memory.append(CodeStep(code))
                    log_entry["steps"].append({"type": "code", "content": code})
                    
                    yield yield_content(f"\nrunning code ({attempt_label})... 🏃")
                    
                    # Execute Code
                    exec_start = time.time()
                    execution_result = ""
                    execution_error = None
                    
                    # Generator-based code execution handling
                    exec_gen = self._execute_code_generator(code)
                    
                    try:
                        for chunk in exec_gen:
                            # We might get strings (stdout) or Exceptions
                            if isinstance(chunk, Exception):
                                execution_error = chunk
                            else:
                                execution_result += chunk
                                yield yield_content(f"\n{chunk}")
                    except Exception as e:
                        execution_error = e

                    exec_latency = time.time() - exec_start
                    
                    # Store Observation or Error
                    if execution_error:
                        error_msg = str(execution_error)
                        self.memory.append(ErrorStep(error_msg))
                        log_entry["steps"].append({"type": "error", "content": error_msg, "latency": exec_latency})
                        
                        yield yield_content(f"\n⚠️ Execution Error in {attempt_label}: {error_msg}\nTrying to fix...\n")
                        # Loop continues -> Next step will see ErrorStep
                        
                    else:
                        # Success!
                        self.memory.append(ObservationStep(execution_result))
                        log_entry["steps"].append({"type": "execution_trace", "content": execution_result, "latency": exec_latency})
                        
                        total_duration = time.time() - start_time
                        summary = f"\n*(Success in {total_duration:.2f}s)*"
                        yield yield_content(summary)
                        final_success = True
                        break # Break the loop on success
                
                else:
                    # No code generated -> Pure Chat Response?
                    # Consider this success if it's just an answer
                    yield yield_content(f"\n(No code generated, assuming direct answer)\n")
                    final_success = True
                    break
                    
            except Exception as e:
                yield yield_content(f"\n[!] System Error: {e}\n")
                break
                
            step_count += 1

        if not final_success and step_count == self.max_steps:
             yield yield_content(f"\n[!] Failed to solve task after {self.max_steps} attempts.\n")
             
        # Save Log
        # Save Log (Append to Session JSONL)
        # log_file was defined at start of run()
        try:
             with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
             print(f"DEBUG: Appended log to {log_file}")
        except Exception as e:
            print(f"DEBUG: Failed to write log: {e}")


    # Helper to run code and yield output chunks
    def _execute_code_generator(self, code: str):
        yield f"""
<details>
<summary>💻 Code Execution (Click to expand)</summary>
```python
{code}
```
"""
        import io, sys
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        
        exec_globals = {"__name__": "__main__", "print": print}
        
        # Tool Logging Wrapper
        def make_logged_tool(tool_name, tool_func):
            def logged_wrapper(*args, **kwargs):
                arg_str = ", ".join([repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()])
                print(f"🔧 [Tool Call] {tool_name}({arg_str})")
                try:
                    res = tool_func(*args, **kwargs)
                    res_str = str(res)
                    if len(res_str) > 200: res_str = res_str[:200] + "... (truncated)"
                    print(f"   -> [Result] {res_str}")
                    return res
                except Exception as e:
                    print(f"   -> [Error] {e}")
                    raise e
            return logged_wrapper

        for name, tool in self.tools.items():
            exec_globals[name] = make_logged_tool(name, tool.func)
            
        try:
            exec(code, exec_globals)
            sys.stdout = old_stdout
            result = redirected_output.getvalue()
            
            # Format Output
            lines = result.split('\n')
            logs = [l for l in lines if l.strip().startswith(('🔧', '[*]', '->', '   ->', '[!]'))]
            output = [l for l in lines if l not in logs]
            
            log_str = "\n".join(logs).strip()
            output_str = "\n".join(output).strip()
            
            # Close Code Block Details immediately
            yield "</details>\n"
            
            if log_str:
                yield f"<details><summary>🛠️ Execution Logs</summary>```text\n{log_str}\n```</details>\n"
            
            if output_str:
                yield f"\n### 🏁 Result\n{output_str}\n"
            else:
                yield "\n*(No text output)*\n"
            
        except Exception as e:
            sys.stdout = old_stdout
            yield "</details>\n"
            yield f"### ❌ Execution Error\n```text\n{e}\n```\n"
            yield e # Yield exception object to caller to signal failure
