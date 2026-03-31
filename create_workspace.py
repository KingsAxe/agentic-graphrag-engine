import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.postgres import async_session, engine
from src.models.workspace import Base, Workspace
from src.models.document import Document, IngestionJob
import uuid

async def create_workspace():
    # Create tables
    async with engine.begin() as conn:
        from src.models.workspace import Base as WBase
        from src.models.document import Base as DBase
        # We need to recreate tables or just run create_all
        await conn.run_sync(WBase.metadata.create_all)
        await conn.run_sync(DBase.metadata.create_all)
    
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Workspace).where(Workspace.name == "Dev Test Workspace"))
        ws = result.scalars().first()
        
        if not ws:
            api_key = "rag-dev-123456789"
            ws = Workspace(name="Dev Test Workspace", api_key=api_key)
            session.add(ws)
            await session.commit()
            print(f"SUCCESS: Created Workspace! Your Test API Key is: Bearer {api_key}")
        else:
            print(f"SUCCESS: Workspace exists! Your Test API Key is: Bearer {ws.api_key}")

if __name__ == "__main__":
    asyncio.run(create_workspace())
