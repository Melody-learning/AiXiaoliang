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
# Configure GenAI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"), transport="rest")

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
    def __init__(self, model_name: str = "gemini-3-flash-preview", tools: List[Any] = []):
        self.model_name = model_name
        self.tools = {tool.name: tool for tool in tools}
        print(f"DEBUG: Loaded tools: {list(self.tools.keys())}")
        self.memory: List[Step] = []
        self.max_steps = 15  # Allow up to 15 steps (Self-Correction)
        
        # Capture System/Env Proxy for isolation (Ping-Pong Strategy)
        self.sys_http_proxy = os.getenv("HTTP_PROXY")
        self.sys_https_proxy = os.getenv("HTTPS_PROXY")

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
2. **Use only the tools listed above.** Do not invent new function names.

### CRITICAL RULES (MUST FOLLOW)

**Rule #1: ENVELOPE PROTOCOL (Rich Signals Pattern)**
All tools now return a standard **Response Envelope** (Dict). You MUST parse it:
```python
res = tool_function(...)
# Envelope Structure: {{'status': 'success'|'empty'|'error', 'data': ..., 'meta': {{'hint': ...}}}}

if res['status'] == 'success':
    data = res['data'] 
    # Use data...
elif res['status'] == 'empty':
    # MUST read the hint. Do NOT retry blindly.
    print(f"Empty: {{res['meta'].get('hint')}}")
    # Example: If hint says "Try previous day", you MUST query yesterdays date immediately.
elif res['status'] == 'error':
    print(f"Error: {{res.get('error')}}")
```
**NEVER** assume the tool returns a list directly. ALWAYS check `status`.

**Rule #2: NO GUESSING OF KEYS.** 
If the user asks for financial indicators (PE, Dividend, etc.):
- **MUST** call `search_knowledge(query)` first.
- **Yield after search** (Action -> Observation -> Logic).



**Rule #3: TERMINATION**
- When you have successfully printed the final answer to the user, **STOP writing code**.
- Output only a "Thought" summarizing the result.
- If you continue writing code, the loop will never end.

**Rule #4: DEFENSIVE CODING**
- DO NOT assume the structure of `res['data']` (Dict vs List vs String).
- **ALWAYS** inspect unfamiliar data first: `print(res['data'])` or `print(type(res['data']))`.
- **NEVER** write `res['data']['key']` or `res['data'][0]` without verifying the structure first.
- If `status` is 'success' but you are unsure of the schema, PRINT IT before accessing it.


### One-Shot Example (Envelope Pattern)
User: "Check Maotai's PE."
Thought: Search keys first.
Code:
```python
print(search_knowledge("PE key"))
```
Observation: Key is 'pe_ttm'.
Thought: Fetch data and handle envelope.
Code:
```python
res = get_fundamentals_data('600519.SH')
if res['status'] == 'success':
    print(f"PE: {{res['data']['pe_ttm']}}")
else:
    print(f"No data: {{res.get('meta')}}")
```"""

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


    def run(self, user_input: str, history: List[str] = [], stream_mode: str = "delta", session_id: str = None, log_subdir: str = ""):
        full_buffer = ""
        trace_md = "" # Aggregates all reasoning steps
        final_answer = ""
        
        def yield_content(chunk, replace=False):
            nonlocal full_buffer
            if replace:
                full_buffer = chunk
            else:
                full_buffer += chunk
            return full_buffer if stream_mode == "full" else chunk

        def render_display(is_final=False):
            """Helper to render the current trace + final answer"""
            status_attr = "" if is_final else "open"
            accordion = f"<details {status_attr}>\n<summary>💡 思考过程 (点击展开)</summary>\n\n{trace_md}\n</details>"
            if is_final:
                return f"{accordion}\n\n{final_answer}"
            return accordion

        # Reset Memory for this run
        self.memory = [TaskStep(user_input)]
        
        # Session Logging Setup
        if not session_id:
            session_id = f"session_{int(time.time())}"
            
        log_dir = os.path.join("logs", log_subdir) if log_subdir else "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f"{session_id}.jsonl")
        
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": user_input,
            "steps": []
        }
            
        start_time = time.time()
        step_count = 0
        final_success = False
        
        trace_md += f"Thinking about '{user_input}'... (Attempt 1)\n"
        yield yield_content(render_display(), replace=True)

        try:
            while step_count < self.max_steps:
                try:
                    prompt = self._build_prompt_from_memory(history)
                    
                    # Call LLM
                    llm_start = time.time()
                    # Restore System Proxy
                    if self.sys_http_proxy:
                        os.environ["HTTP_PROXY"] = self.sys_http_proxy
                    else:
                        os.environ.pop("HTTP_PROXY", None)
                        
                    if self.sys_https_proxy:
                        os.environ["HTTPS_PROXY"] = self.sys_https_proxy
                    else:
                        os.environ.pop("HTTPS_PROXY", None)

                    model = genai.GenerativeModel(self.model_name)
                    response = model.generate_content(prompt)
                    llm_latency = time.time() - llm_start
                    
                    if not response.parts:
                        err = "[!] Empty Response from Model."
                        trace_md += f"\n{err}\n"
                        yield yield_content(render_display(), replace=True)
                        break
                        
                    content = response.text
                    self.memory.append(ThoughtStep(content))
                    log_entry["steps"].append({"type": "thought", "content": content, "latency": llm_latency, "attempt": step_count+1})
                    
                    # Extract Code
                    code_match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
                    
                    if code_match:
                        # If it has code, it's a reasoning step, add to trace
                        attempt_label = f"Step {step_count+1}"
                        trace_md += f"\n#### 🧠 {attempt_label}\n{content}\n"
                        trace_md += f"\n> 🏃 正在执行代码...\n"
                        yield yield_content(render_display(), replace=True)
                        
                        code = code_match.group(1)
                        self.memory.append(CodeStep(code))
                        log_entry["steps"].append({"type": "code", "content": code})
                        
                        # Execute Code
                        exec_start = time.time()
                        execution_result = ""
                        execution_error = None
                        
                        exec_gen = self._execute_code_generator(code)
                        
                        try:
                            for chunk in exec_gen:
                                if isinstance(chunk, Exception):
                                    execution_error = chunk
                                else:
                                    execution_result += chunk
                                    trace_md += chunk
                                    yield yield_content(render_display(), replace=True)
                        except Exception as e:
                            execution_error = e

                        exec_latency = time.time() - exec_start
                        
                        if execution_error:
                            error_msg = str(execution_error)
                            self.memory.append(ErrorStep(error_msg))
                            log_entry["steps"].append({"type": "error", "content": error_msg, "latency": exec_latency})
                            trace_md += f"\n⚠️ 执行错误: {error_msg}\n正在尝试修复...\n"
                            yield yield_content(render_display(), replace=True)
                        else:
                            self.memory.append(ObservationStep(execution_result))
                            log_entry["steps"].append({"type": "execution_trace", "content": execution_result, "latency": exec_latency})
                            
                            if self._is_suspicious_output(execution_result):
                                warning_msg = "System Warning: Output appears invalid. Self-Correction Triggered."
                                self.memory.append(ObservationStep(warning_msg))
                                trace_md += f"\n⚠️ {warning_msg}\n"
                                yield yield_content(render_display(), replace=True)
                            else:
                                total_duration = time.time() - start_time
                                trace_md += f"\n*(Step success in {total_duration:.2f}s)*\n"
                                yield yield_content(render_display(), replace=True)
                    
                    else:
                        # Final Answer Found (No code block)
                        # Clean up "Thought: " or "Final Answer: " prefixes
                        cleaned_answer = re.sub(r"^(Thought|Final Answer|总结|回答):\s*", "", content, flags=re.IGNORECASE | re.MULTILINE).strip()
                        final_answer = cleaned_answer
                        
                        # Add a final label to trace for completion
                        trace_md += f"\n#### ✅ 任务完成\n{content}\n"
                        final_success = True
                        break
                        
                except Exception as e:
                    trace_md += f"\n[!] System Error: {e}\n"
                    yield yield_content(render_display(), replace=True)
                    break
                    
                step_count += 1

            if not final_success and step_count == self.max_steps:
                 trace_md += f"\n[!] Failed to solve task after {self.max_steps} attempts.\n"
            
            # Final Yield: Collapsed
            yield yield_content(render_display(is_final=True), replace=True)

        finally:
            # Save Log (This will now run even if GeneratorExit is triggered)
            try:
                 with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                 print(f"DEBUG: Appended log to {log_file}")
            except Exception as e:
                print(f"DEBUG: Failed to write log: {e}")



    def _is_suspicious_output(self, output: str) -> bool:
        """
        Heuristic check: Return True if output seems to indicate failure despite no Exception.
        """
        # 1. Explicit 'None' in output (common Python null print)
        # (Deleted 'None' check to prevent false positives with dictionaries)

        # 2. Empty output (stripped of HTML tags)
        clean_out = re.sub(r'<[^>]+>', '', output).strip()
        if not clean_out: 
             return True
        return False

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
