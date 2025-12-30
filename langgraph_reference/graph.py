
from langgraph.graph import StateGraph, END
from .state import AgentState

# Node: Reason (LLM)
def reason_node(state: AgentState):
    messages = state['messages']
    # Call LLM ...
    # response = llm.invoke(messages)
    # return {"messages": [response]}
    pass

# Node: Action (Tools)
def action_node(state: AgentState):
    # Retrieve last message (tool call)
    last_message = state['messages'][-1]
    # Execute tool ...
    # return {"messages": [ToolMessage(...)]}
    pass

# Conditional Edge: Router
def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    # If LLM stopped or no tool call -> End
    if "tool_calls" not in last_message or not last_message.tool_calls:
        return "end"
    return "continue"

# Graph Construction
workflow = StateGraph(AgentState)
workflow.add_node("agent", reason_node)
workflow.add_node("action", action_node)

workflow.set_entry_point("agent")

# The Loop: Agent -> Router -> Action -> Agent
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)
workflow.add_edge("action", "agent") # Loop back to agent after action

app = workflow.compile()
