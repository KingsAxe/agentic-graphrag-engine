from neo4j import AsyncGraphDatabase
from src.core.config import settings

neo4j_driver = AsyncGraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)

async def get_neo4j_session():
    async with neo4j_driver.session() as session:
        yield session
