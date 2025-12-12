from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
import inspect

@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        
    def register(self, name: str = None, description: str = None):
        """Decorator to register a function as a tool."""
        def decorator(func):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or "No description provided."
            self._tools[tool_name] = Tool(tool_name, tool_desc, func)
            return func
        return decorator
        
    def get_tools(self):
        return list(self._tools.values())
        
    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

# Global registry instance
default_registry = ToolRegistry()
register_tool = default_registry.register
