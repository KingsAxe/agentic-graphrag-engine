import logging
import operator
from datetime import datetime, timezone
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from neo4j.exceptions import ServiceUnavailable
from src.core.config import settings
from src.services.agent.tools import search_vector_tool, query_graph_tool, expand_entity_tool
from src.services.llm.factory import build_chat_llm, get_llm_display_name, llm_is_configured
from src.services.neo4j_service import Neo4jService
from src.services.qdrant_service import QdrantService
from src.services.ingestion.embedder import get_embedder

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    workspace_id: str

tools = [search_vector_tool, query_graph_tool, expand_entity_tool]
tool_node = ToolNode(tools)
logger = logging.getLogger(__name__)


def _trace_event(step: str, title: str, detail: str, status: str = "completed") -> dict:
    return {
        "step": step,
        "title": title,
        "detail": detail,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_mock_agent_with_trace(query: str, workspace_id: str):
    logger.info("Running mock agent workflow for workspace %s", workspace_id)
    trace = [
        _trace_event("receive_query", "Query Received", f"Workspace {workspace_id} submitted: {query}"),
    ]

    try:
        graph_hits = await Neo4jService.query_graph(workspace_id, query)
        trace.append(
            _trace_event(
                "graph_lookup",
                "Graph Lookup",
                f"Neo4j lookup returned {len(graph_hits)} graph matches.",
            )
        )
    except ServiceUnavailable:
        logger.warning("Neo4j is unavailable. Mock agent will continue with vector search only.")
        graph_hits = []
        trace.append(
            _trace_event(
                "graph_lookup",
                "Graph Lookup Skipped",
                "Neo4j is unavailable, so graph reasoning is temporarily skipped.",
                status="warning",
            )
        )

    query_vector = get_embedder().embed_texts([query])[0]
    vector_hits = await QdrantService.search_chunks(workspace_id, query_vector)
    trace.append(
        _trace_event(
            "vector_lookup",
            "Vector Retrieval",
            f"Qdrant returned {len(vector_hits)} candidate chunks for the query.",
        )
    )

    lines = [f"Mock agent response for query: {query}"]

    if graph_hits:
        lines.append("Graph matches:")
        for hit in graph_hits[:3]:
            lines.append(f"- {hit['id']} ({hit['type']}): {hit['description']}")

        try:
            expanded = await Neo4jService.expand_entity(workspace_id, graph_hits[0]["id"])
            claims = expanded.get("claims", [])
            if claims:
                lines.append("Claims:")
                for claim in claims[:3]:
                    lines.append(f"- {claim['claim']}")
        except ServiceUnavailable:
            lines.append("Neo4j claims are unavailable because the graph database is offline.")

    if vector_hits:
        lines.append("Relevant chunks:")
        for hit in vector_hits[:3]:
            lines.append(f"- score={hit['score']:.3f} text={hit['text'][:180]}")

    if not graph_hits and not vector_hits:
        lines.append("No matching knowledge was found in the local stores yet.")

    lines.append("This is a mock development response and does not use an actual LLM.")
    trace.append(
        _trace_event(
            "compose_response",
            "Response Assembly",
            "The mock agent composed the final answer from the available retrieval results.",
        )
    )
    return {
        "response": "\n".join(lines),
        "trace": trace,
    }

def get_app():
    if settings.LLM_PROVIDER.lower() == "mock":
        return None

    if not llm_is_configured():
        logger.warning("Skipping agent app initialization because the LLM provider is not configured")
        return None

    logger.info("Initializing agent orchestrator with %s", get_llm_display_name())
    model = build_chat_llm(temperature=0)
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

async def run_agent_with_trace(query: str, workspace_id: str):
    if settings.LLM_PROVIDER.lower() == "mock":
        return await run_mock_agent_with_trace(query, workspace_id)

    if not app:
        logger.error("Cannot run agent because the LLM provider is not configured")
        raise ValueError("Cannot run agent: the configured LLM provider is not ready.")

    inputs = {
        "messages": [HumanMessage(content=f"User Query: {query}\n(Internal context: workspace_id={workspace_id})")],
        "workspace_id": workspace_id
    }

    trace = [
        _trace_event("receive_query", "Query Received", f"Workspace {workspace_id} submitted: {query}"),
        _trace_event("agent_start", "Agent Workflow", f"Running LangGraph workflow with {get_llm_display_name()}."),
    ]

    logger.info("Running agent workflow for workspace %s", workspace_id)
    final_state = await app.ainvoke(inputs)
    response = final_state["messages"][-1].content
    trace.append(
        _trace_event(
            "agent_complete",
            "Agent Complete",
            "The workflow returned a final answer to the API layer.",
        )
    )

    return {
        "response": response,
        "trace": trace,
    }

async def run_agent(query: str, workspace_id: str):
    result = await run_agent_with_trace(query, workspace_id)
    return result["response"]
