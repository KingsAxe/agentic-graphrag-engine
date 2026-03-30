# ADR-002: Agent Orchestration Framework

**Status:** Proposed  
**Date:** 2026-03-30  
**Deciders:** Engineering Lead

---

## Context

The Agent Service is the reasoning core of SovereignRAG V2. It receives a user query, selects and
executes tools (`search_vector`, `query_graph`, `expand_entity`, `validate_claim`), and assembles
a structured response with evidence and a reasoning path.

The quality of the agent design has significant downstream consequences: it determines how
reasoning traces are captured, how tool calls are sequenced, and how easy it is to add new
capabilities over time. The framework choice also determines how much infrastructure the team
owns vs. delegates to an external library.

---

## Decision Drivers

- Must support multi-step, conditional tool use
- Must produce inspectable reasoning traces (not a black box)
- Must be extensible — new tools will be added in V2.2 and V2.3
- Must integrate with any LLM provider (local or external API)
- Should be debuggable and testable at the unit level
- Should not introduce framework lock-in that complicates the fine-tuning phase

---

## Options Considered

### Option A: Custom Agent Loop

Build a bespoke agent loop in Python. The agent follows a structured ReAct-style
(Reason, Act, Observe) iteration: the LLM produces a thought and tool call, the system
executes the tool, the result is appended to context, and the loop continues until a stop
condition is met.

**Architecture sketch:**
```
AgentRunner
  └── ReActLoop
        ├── think(context) -> Thought + ToolCall
        ├── execute(tool_call) -> Observation
        ├── append_to_context(observation)
        └── check_stop_condition()
```

| Factor | Assessment |
|---|---|
| Reasoning trace visibility | Full — every thought, action, observation is owned code |
| LLM provider flexibility | Full — no framework assumptions |
| Tool extensibility | High — tools are plain Python callables |
| Debuggability | High — straightforward to unit-test each component |
| Framework lock-in | None |
| Development effort | High — loop logic, error handling, retry logic all hand-built |
| Community/docs support | None — internal only |
| Portfolio signal | Strong — demonstrates deep systems understanding |

**Risks:** Requires building robust error handling, tool call parsing, context window management,
and retry logic from scratch. This is a significant time investment in V2.1.

---

### Option B: LangGraph

A graph-based agent orchestration framework from LangChain. The agent is modeled as a directed
graph of nodes (functions) connected by conditional edges. State is passed between nodes as a
typed dictionary.

**Architecture sketch:**
```
StateGraph
  ├── node: retrieve
  ├── node: reason
  ├── node: validate
  ├── edge: retrieve -> reason (always)
  └── edge: reason -> validate (if confidence < threshold)
             reason -> END (if confidence >= threshold)
```

| Factor | Assessment |
|---|---|
| Reasoning trace visibility | Good — LangSmith integration for tracing |
| LLM provider flexibility | Good — LangChain supports most providers |
| Tool extensibility | Good — tool nodes are standard functions |
| Debuggability | Medium — graph state can be opaque; LangSmith helps |
| Framework lock-in | Moderate — LangGraph patterns are idiomatic, migration costly |
| Development effort | Low-Medium — graph primitives handle loop logic |
| Community/docs support | Strong — large ecosystem |
| Portfolio signal | Moderate — "used LangGraph" is table stakes in 2026 |

**Risks:** LangGraph has a steeper conceptual model than a simple loop. The LangChain ecosystem
has a history of rapid API changes. Lock-in is real if the graph model becomes deeply embedded.

---

### Option C: LlamaIndex Workflows

LlamaIndex provides a `Workflow` abstraction that orchestrates agent steps as events passed
between async step functions. It has tight integration with LlamaIndex's own indexing and
retrieval primitives.

| Factor | Assessment |
|---|---|
| Reasoning trace visibility | Moderate — event system provides some observability |
| LLM provider flexibility | Good — but LlamaIndex abstractions encourage its own patterns |
| Tool extensibility | Good within LlamaIndex ecosystem |
| Debuggability | Medium |
| Framework lock-in | High — deeply coupled to LlamaIndex retrieval stack |
| Development effort | Low for LlamaIndex-native retrieval |
| Community/docs support | Strong |
| Portfolio signal | Moderate |

**Risks:** The deepest lock-in of the three options. The retrieval stack would become tied to
LlamaIndex patterns, which conflicts with the custom Retrieval Service and Graph Service already
designed. Also conflicts with the planned custom fine-tuning pipeline.

---

## Comparison Summary

| Criterion | Custom Loop | LangGraph | LlamaIndex |
|---|---|---|---|
| Trace visibility | Highest | High (with tooling) | Medium |
| LLM portability | Full | Good | Good |
| Tool extensibility | Full | Good | Good |
| Dev effort (V2.1) | High | Medium | Low-Medium |
| Framework lock-in | None | Moderate | High |
| Portfolio signal | Highest | Medium | Medium |
| Debuggability | Highest | Medium | Medium |

---

## Recommendation

**LangGraph for the orchestration skeleton, with custom tool implementations.**

A fully custom loop is the intellectually correct choice for a portfolio system and for long-term
flexibility, but the development cost in V2.1 is significant. LangGraph provides the graph
primitives that handle state management, conditional routing, and loop termination — all of which
are non-trivial to implement robustly from scratch.

The critical constraint is: **all tools (`search_vector`, `query_graph`, `expand_entity`,
`validate_claim`) must be implemented as standard Python functions with no LangGraph dependency**.
The graph is the orchestrator; the services are framework-agnostic. This preserves portability
and keeps the portfolio signal high.

LlamaIndex is not recommended — the retrieval lock-in directly conflicts with the custom service
architecture already defined.

---

## Decision

**[ ] Custom Agent Loop**  
**[ ] LangGraph (with framework-agnostic tools)**  
**[ ] LlamaIndex Workflows**  

_Mark the selected option and update status to "Accepted" when decided._
