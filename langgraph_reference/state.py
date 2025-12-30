
from typing import TypedDict, Annotated, List, Union
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The state of the agent in the graph.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    # In 2025 best practices, we explicit track 'next_step' or 'errors' in state
    next_step: str 
