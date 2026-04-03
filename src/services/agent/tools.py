from langchain_core.tools import tool
from src.services.qdrant_service import QdrantService
from src.services.neo4j_service import Neo4jService
from src.services.ingestion.embedder import get_embedder
from src.services.validation.engine import get_validation_engine
import asyncio

@tool
def search_vector_tool(query: str, workspace_id: str):
    """Search for relevant text chunks using semantic vector search. 
    Use this for general factual questions and broad context."""
    embedder = get_embedder()
    query_vector = embedder.embed_texts([query])[0]
    results = asyncio.run(QdrantService.search_chunks(workspace_id, query_vector))
    return results

@tool
def query_graph_tool(query_text: str, workspace_id: str):
    """Search the knowledge graph for specific entities and their high-level descriptions.
    Use this when looking for specific names, organizations, or concepts."""
    results = asyncio.run(Neo4jService.query_graph(workspace_id, query_text))
    return results

@tool
def expand_entity_tool(entity_id: str, workspace_id: str):
    """Retrieve all relationships and detailed claims for a specific entity ID.
    This tool also performs a validation check on the claims to detect contradictions 
    and compute a confidence score. Use this for deep-dives into an entity."""
    
    async def _run():
        results = await Neo4jService.expand_entity(workspace_id, entity_id)
        
        # Run Validation on claims
        engine = get_validation_engine()
        validation = await engine.validate_claims(results.get("claims", []))
        
        results["validation"] = validation
        return results

    return asyncio.run(_run())
