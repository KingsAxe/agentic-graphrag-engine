import logging
from src.db.neo4j_client import neo4j_driver
from src.models.graph import GraphExtraction

logger = logging.getLogger(__name__)

class Neo4jService:
    @staticmethod
    async def merge_chunk(workspace_id: str, document_id: str, chunk_index: int, text: str):
        query = """
        MERGE (c:Chunk {id: $chunk_id})
        SET c.workspace_id = $workspace_id,
            c.document_id = $document_id,
            c.text = $text
        """
        chunk_id = f"{document_id}_{chunk_index}"
        async with neo4j_driver.session() as session:
            await session.run(query, chunk_id=chunk_id, workspace_id=workspace_id, document_id=document_id, text=text)

    @staticmethod
    async def insert_extraction(workspace_id: str, document_id: str, chunk_index: int, extraction: GraphExtraction):
        if not extraction.entities and not extraction.claims:
            return

        chunk_id = f"{document_id}_{chunk_index}"
        
        async with neo4j_driver.session() as session:
            # 1. Merge Entities and link them to the Chunk
            for entity in extraction.entities:
                query = """
                MATCH (c:Chunk {id: $chunk_id})
                MERGE (e:Entity {id: $ent_id, workspace_id: $workspace_id})
                SET e.type = $ent_type, e.description = $ent_desc
                MERGE (c)-[:MENTIONS]->(e)
                """
                await session.run(
                    query, 
                    chunk_id=chunk_id, 
                    ent_id=entity.id.upper(), 
                    workspace_id=workspace_id,
                    ent_type=entity.type.upper(),
                    ent_desc=entity.description
                )

            # 2. Merge Relationships (Direct Cypher String interpolation for relationship types)
            for rel in extraction.relationships:
                safe_rel_type = "".join(c for c in rel.relation_type.upper() if c.isalnum() or c == '_')
                if safe_rel_type:
                    query = f"""
                    MATCH (source:Entity {{id: $source_id, workspace_id: $workspace_id}})
                    MATCH (target:Entity {{id: $target_id, workspace_id: $workspace_id}})
                    MERGE (source)-[r:{safe_rel_type}]->(target)
                    SET r.description = $desc
                    """
                    await session.run(
                        query, 
                        source_id=rel.source_entity_id.upper(), 
                        target_id=rel.target_entity_id.upper(),
                        workspace_id=workspace_id,
                        desc=rel.description
                    )

            # 3. Merge Claims
            for claim in extraction.claims:
                query = """
                MATCH (c:Chunk {id: $chunk_id})
                MATCH (e:Entity {id: $subject_id, workspace_id: $workspace_id})
                MERGE (claim:Claim {text: $claim_text})
                MERGE (e)-[:HAS_CLAIM]->(claim)
                MERGE (c)-[:SUPPORTS]->(claim)
                """
                await session.run(
                    query,
                    chunk_id=chunk_id,
                    subject_id=claim.subject_entity_id.upper(),
                    workspace_id=workspace_id,
                    claim_text=claim.claim
                )

    @staticmethod
    async def query_graph(workspace_id: str, query_text: str):
        """Search for entities matching a text query within a workspace."""
        cypher = """
        MATCH (e:Entity {workspace_id: $workspace_id})
        WHERE e.id CONTAINS $search_text OR e.description CONTAINS $search_text
        RETURN e.id as id, e.type as type, e.description as description
        LIMIT 10
        """
        async with neo4j_driver.session() as session:
            result = await session.run(
                cypher,
                workspace_id=workspace_id,
                search_text=query_text.upper(),
            )
            return [record.data() for record in await result.data()]

    @staticmethod
    async def expand_entity(workspace_id: str, entity_id: str):
        """Retrieve all relationships and claims for a specific entity with metadata."""
        rel_query = """
        MATCH (source:Entity {id: $ent_id, workspace_id: $workspace_id})-[r]->(target:Entity {workspace_id: $workspace_id})
        RETURN source.id as source, type(r) as relation, target.id as target, r.description as description
        """
        claim_query = """
        MATCH (e:Entity {id: $ent_id, workspace_id: $workspace_id})-[:HAS_CLAIM]->(claim:Claim)
        MATCH (c:Chunk)-[:SUPPORTS]->(claim)
        RETURN claim.text as claim, count(c) as support_count, collect(DISTINCT c.document_id) as document_ids
        """
        async with neo4j_driver.session() as session:
            rel_result = await session.run(rel_query, ent_id=entity_id.upper(), workspace_id=workspace_id)
            claim_result = await session.run(claim_query, ent_id=entity_id.upper(), workspace_id=workspace_id)
            
            return {
                "relationships": [record.data() for record in await rel_result.data()],
                "claims": [record.data() for record in await claim_result.data()]
            }

    @staticmethod
    async def delete_workspace_graph(workspace_id: str):
        query = """
        MATCH (n {workspace_id: $workspace_id})
        OPTIONAL MATCH (n)-[]-(claim:Claim)
        WITH collect(DISTINCT n) + collect(DISTINCT claim) AS nodes
        UNWIND nodes AS node
        WITH DISTINCT node
        WHERE node IS NOT NULL
        DETACH DELETE node
        """
        async with neo4j_driver.session() as session:
            await session.run(query, workspace_id=workspace_id)
