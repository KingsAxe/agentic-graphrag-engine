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
