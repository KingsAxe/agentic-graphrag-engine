import asyncio
import os
import sys
import uuid

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.qdrant_service import QdrantService
from src.services.neo4j_service import Neo4jService
from src.services.agent.orchestrator import run_agent
from src.db.postgres import async_session
from src.models.workspace import Workspace
from sqlalchemy import select

async def setup_test_data(workspace_id: str):
    print("--- Setting up test data ---")
    
    # 1. Mock data for Qdrant
    # BGE-M3 uses 1024 dims. We'll just use a dummy vector.
    dummy_vector = [0.1] * 1024
    doc_id = str(uuid.uuid4())
    chunks = ["The CEO of Acme Corp is Alice Smith. Acme Corp was founded in 2020."]
    
    await QdrantService.init_collection()
    await QdrantService.upsert_chunks(workspace_id, doc_id, chunks, [dummy_vector])
    print("Qdrant data inserted.")

    # 2. Mock data for Neo4j
    # We need a Chunk node first
    await Neo4jService.merge_chunk(workspace_id, doc_id, 0, chunks[0])
    
    from src.models.graph import GraphExtraction, Entity, Relationship, Claim
    extraction = GraphExtraction(
        entities=[
            Entity(id="ACME_CORP", type="ORGANIZATION", description="A fictional technology company."),
            Entity(id="ALICE_SMITH", type="PERSON", description="The CEO of Acme Corp.")
        ],
        relationships=[
            Relationship(source_entity_id="ALICE_SMITH", target_entity_id="ACME_CORP", relation_type="WORKS_FOR", description="Alice Smith is the CEO.")
        ],
        claims=[
            Claim(subject_entity_id="ACME_CORP", claim="Acme Corp was founded in 2020.")
        ]
    )
    await Neo4jService.insert_extraction(workspace_id, doc_id, 0, extraction)
    print("Neo4j data inserted.")

async def verify():
    print("Starting Week 4 Verification...")
    
    # Get workspace
    async with async_session() as session:
        result = await session.execute(select(Workspace).where(Workspace.name == "Dev Test Workspace"))
        ws = result.scalars().first()
        if not ws:
            print("Error: Run create_workspace.py first.")
            return
        workspace_id = str(ws.id)

    await setup_test_data(workspace_id)

    print("\n--- Testing Qdrant Search ---")
    # Check if it returns results
    dummy_query_vector = [0.1] * 1024
    q_results = await QdrantService.search_chunks(workspace_id, dummy_query_vector)
    print(f"Qdrant results found: {len(q_results)}")
    if q_results:
        print(f"Top result: {q_results[0]['text']}")

    print("\n--- Testing Neo4j Query ---")
    n_results = await Neo4jService.query_graph(workspace_id, "ACME")
    print(f"Neo4j Query results: {n_results}")

    print("\n--- Testing Neo4j Expand ---")
    e_results = await Neo4jService.expand_entity(workspace_id, "ACME_CORP")
    print(f"Neo4j Expand results: {e_results}")

    print("\n--- Testing Agent (requires API Key) ---")
    try:
        agent_response = await run_agent("Who is the CEO of Acme Corp and when was it founded?", workspace_id)
        print(f"Agent Response: {agent_response}")
    except Exception as e:
        print(f"Agent failed (expected if API key missing): {e}")

if __name__ == "__main__":
    asyncio.run(verify())
