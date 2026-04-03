from typing import TypedDict, Annotated, Sequence
import operator
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from src.services.agent.tools import search_vector_tool, query_graph_tool, expand_entity_tool
from src.core.config import settings

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    workspace_id: str

tools = [search_vector_tool, query_graph_tool, expand_entity_tool]
tool_node = ToolNode(tools)

def get_app():
    if not settings.GROQ_API_KEY:
        return None

    model = ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=settings.LLM_MODEL,
        temperature=0
    )
    model_with_tools = model.bind_tools(tools)

    def call_model(state: AgentState):
        response = model_with_tools.invoke(state['messages'])
        return {"messages": [response]}

    def should_continue(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()

app = get_app()

async def run_agent(query: str, workspace_id: str):
    if not app:
        raise ValueError("Cannot run agent: GROQ_API_KEY is not set.")
    
    # Initial state
    inputs = {
        "messages": [HumanMessage(content=f"User Query: {query}\n(Internal context: workspace_id={workspace_id})")],
        "workspace_id": workspace_id
    }
    
    final_state = await app.ainvoke(inputs)
    return final_state["messages"][-1].content
