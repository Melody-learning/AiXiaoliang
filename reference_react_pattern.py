
from typing import List, Dict, Any, Optional
import re

class ReActAgent:
    """
    A Minimal, Clean Implementation of the ReAct (Reasoning + Acting) Pattern.
    Based on 2025 Best Practices (smolagents, LangGraph styles).
    """
    def __init__(self, llm, tools, max_steps: int = 10):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
        self.memory: List[Dict] = []
        
    def run(self, query: str):
        self.memory = [{"role": "system", "content": self._system_prompt()}, 
                       {"role": "user", "content": query}]
        
        step_count = 0
        while step_count < self.max_steps:
            step_count += 1
            print(f"--- Step {step_count} ---")
            
            # 1. THOUGHT & ACTION GENERATION
            response = self.llm.generate(self.memory)
            self.memory.append({"role": "assistant", "content": response})
            print(f"Agent: {response}")
            
            # 2. STOPPING CRITERIA (Final Answer)
            if self._is_final_answer(response):
                return self._extract_final_answer(response)
            
            # 3. ACTION PARSING
            tool_name, tool_args = self._parse_tool_call(response)
            
            if not tool_name:
                # Middleware: No tool call detected but no final answer? 
                # In 2025 Architecture, we trigger a "Reflection" or "Clarification"
                # For now, we assume it's just a chat response (soft stop)
                print("No tool call, assuming chat response.")
                return response
                
            # 4. OBSERVATION (Execution)
            try:
                print(f"Executing: {tool_name}({tool_args})")
                tool = self.tools.get(tool_name)
                if not tool:
                    raise ValueError(f"Tool {tool_name} not found.")
                    
                result = tool.run(**tool_args)
                observation = f"Observation: {str(result)}"
                
            except Exception as e:
                observation = f"Observation: Error executing {tool_name}: {e}"
                
            # 5. OBSERVATION INJECTION & LOOP CONTINUATION
            print(observation)
            self.memory.append({"role": "user", "content": observation})
            
            # Middleware: Observation Enrichment (e.g., Logic-Aware Reflection)
            if "None" in observation or "Error" in observation:
                 self.memory.append({"role": "system", "content": "System Tip: The previous tool call returned an error or empty result. Please verify your inputs."})
                 
        return "Max steps reached."

    def _system_prompt(self):
        return """
Answer the user's question using the ReAct pattern.
Format your response as:
Thought: ...
Action: tool_name(args)
Observation: ... (System will provide this)
...
Thought: ...
Final Answer: ...
"""

    def _is_final_answer(self, text):
        return "Final Answer:" in text

    def _extract_final_answer(self, text):
        return text.split("Final Answer:")[-1].strip()

    def _parse_tool_call(self, text):
        # Simplified parser
        match = re.search(r"Action: (\w+)\((.*)\)", text)
        if match:
            return match.group(1), match.group(2)
        return None, None
