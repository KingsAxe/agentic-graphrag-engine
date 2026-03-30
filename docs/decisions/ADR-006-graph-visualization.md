# ADR-006: Graph Visualization Library

**Status:** Proposed  
**Date:** 2026-03-30  
**Deciders:** Engineering Lead

---

## Context

Graph visualization is a planned V2.4 feature and a core differentiator in the frontend.
The knowledge graph built by SovereignRAG V2 — with its entities, relationships, and claims —
needs to be navigable by end users. The library chosen here determines:

- What types of graph layouts are supported (force-directed, hierarchical, radial)
- How interactive the visualization can be (click to expand, filter by entity type, hover for details)
- How it integrates with Next.js and the frontend data layer
- The rendering performance ceiling (thousands of nodes vs. hundreds)

Although this is a V2.4 deliverable, the decision should be recorded now so the API design
for `GET /graph/entity/{id}` and `POST /graph/query` returns data in a format compatible
with the chosen library from the start.

---

## Decision Drivers

- Must render large graphs (hundreds of nodes, thousands of edges) without browser performance
  degradation
- Must support interactive features: click to expand node neighbors, hover for metadata, filter
  by node/edge type
- Must integrate cleanly with Next.js (React component or wrappable in one)
- Must support custom node and edge styling (entity types should be visually distinct)
- Should support incremental graph updates (adding nodes/edges without full re-render)
- Should have active maintenance

---

## Options Considered

### Option A: Cytoscape.js

A mature, standalone graph theory library with a full rendering engine. Supports hundreds of
layout algorithms, custom node/edge styles, and event-driven interactivity. Has a React wrapper
(`react-cytoscapejs`).

| Factor | Assessment |
|---|---|
| Large graph performance | High — canvas renderer handles thousands of nodes |
| Interactive features | Excellent — extensive event system |
| React/Next.js integration | Good — react-cytoscapejs wrapper |
| Custom styling | Full — CSS-like stylesheet system |
| Incremental updates | Yes — add/remove elements individually |
| Layout algorithms | Extensive — 30+ built-in, including force-directed, hierarchical |
| Bundle size | ~1MB (full), ~400KB (core) |
| Active maintenance | Yes |
| Learning curve | Medium |

**Data format expected:**
```json
{
  "nodes": [{ "data": { "id": "e1", "label": "Entity Name", "type": "Person" } }],
  "edges": [{ "data": { "source": "e1", "target": "e2", "label": "RELATES_TO" } }]
}
```

**Risks:** The React wrapper has occasionally lagged behind Cytoscape.js core releases.
Styling uses a proprietary stylesheet format that has a learning curve.

---

### Option B: D3.js (Force Graph)

D3.js used directly for force-directed graph layout. The de facto standard for custom data
visualizations on the web. Maximum flexibility but requires implementing the graph rendering
layer from scratch.

| Factor | Assessment |
|---|---|
| Large graph performance | Very high — direct SVG/canvas control |
| Interactive features | Unlimited — fully custom |
| React/Next.js integration | Manual — requires refs and useEffect choreography |
| Custom styling | Unlimited |
| Incremental updates | Yes — with manual DOM diffing |
| Layout algorithms | Force simulation only (out of the box) |
| Bundle size | ~250KB (core) |
| Active maintenance | Yes |
| Learning curve | High |

**Data format expected:**
```json
{
  "nodes": [{ "id": "e1", "label": "Entity Name", "type": "Person" }],
  "links": [{ "source": "e1", "target": "e2", "type": "RELATES_TO" }]
}
```

**Risks:** Significant implementation effort. React-D3 integration is notoriously awkward —
D3 mutates the DOM directly, conflicting with React's virtual DOM model. Building a full
graph visualization from D3 primitives for this project would represent a large time investment
for a V2.4 feature.

---

### Option C: react-force-graph

A React-native wrapper around the `force-graph` library, which uses three.js for WebGL-based
rendering. Supports both 2D and 3D graph visualization. Optimized for large graphs.

| Factor | Assessment |
|---|---|
| Large graph performance | Very high — WebGL rendering via three.js |
| Interactive features | Good — node click, hover, zoom, pan |
| React/Next.js integration | Native React component |
| Custom styling | Good — node/edge render functions accept React components |
| Incremental updates | Yes — prop-driven |
| Layout algorithms | Force-directed only (2D and 3D) |
| Bundle size | ~600KB (includes three.js) |
| Active maintenance | Active |
| Learning curve | Low-Medium |

**Data format expected:**
```json
{
  "nodes": [{ "id": "e1", "name": "Entity Name", "type": "Person" }],
  "links": [{ "source": "e1", "target": "e2", "label": "RELATES_TO" }]
}
```

**Risks:** Limited to force-directed layouts. No hierarchical or radial layout support.
Three.js dependency is large. 3D mode may be visually impressive but less useful for
navigating a knowledge graph than a well-configured 2D layout.

---

### Option D: Neovis.js

A Neo4j-specific visualization library built on top of vis.js. Connects directly to a Neo4j
database via the Bolt protocol and renders query results as a graph.

| Factor | Assessment |
|---|---|
| Large graph performance | Moderate — vis.js canvas renderer |
| Interactive features | Good for Neo4j-native workflows |
| React/Next.js integration | Poor — not a React library, requires manual DOM management |
| Custom styling | Limited — vis.js styling |
| Incremental updates | Limited |
| Layout algorithms | Force-directed (vis.js) |
| Bundle size | Moderate |
| Active maintenance | Low — limited recent activity |
| Learning curve | Low (if using Neo4j directly) |

**Risks:** Neovis connects directly to Neo4j, bypassing the API Gateway and all service logic.
This violates the architecture's security model and eliminates the ability to apply workspace
isolation. Not suitable for a multi-tenant system.

---

## Comparison Summary

| Criterion | Cytoscape.js | D3.js | react-force-graph | Neovis.js |
|---|---|---|---|---|
| Large graph performance | High | Very High | Very High | Moderate |
| React integration | Good | Difficult | Native | Poor |
| Layout variety | Excellent | Force only | Force only | Force only |
| Custom styling | Full | Unlimited | Good | Limited |
| Implementation effort | Medium | High | Low | Low |
| Security model compatible | Yes | Yes | Yes | No |
| Active maintenance | Yes | Yes | Yes | Low |

---

## Recommendation

**Cytoscape.js.**

The layout algorithm variety is the decisive factor. A knowledge graph containing entities,
relationships, claims, and their interconnections benefits from hierarchical or radial layouts
in addition to force-directed. Cytoscape.js is the only option that provides this without
additional library dependencies.

The styling system, while having a learning curve, is well-documented and allows entity types
to be visually distinguished clearly — which is critical for the graph exploration feature in V2.4.

Neovis.js must be ruled out: direct database connectivity from the frontend violates the
API Gateway pattern and the workspace isolation model.

The API response format for graph endpoints must conform to the Cytoscape.js element format
from the moment those endpoints are implemented, so no data transformation layer is required
in the frontend.

---

## Decision

**[ ] Cytoscape.js (recommended)**  
**[ ] D3.js**  
**[ ] react-force-graph**  
**[ ] Neovis.js**  

_Mark the selected option and update status to "Accepted" when decided._
