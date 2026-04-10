import asyncio
import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException
from sqlalchemy import select

from src.api.routes.query import _validate_document_scope
from src.db.postgres import async_session
from src.models.document import Document
from src.models.workspace import Workspace
from src.services.qdrant_service import QdrantService


async def get_or_create_workspace(name: str, api_key: str) -> Workspace:
    async with async_session() as session:
        result = await session.execute(select(Workspace).where(Workspace.name == name))
        workspace = result.scalars().first()
        if workspace:
            return workspace

        workspace = Workspace(name=name, api_key=api_key)
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        return workspace


async def create_document(workspace_id, filename: str) -> Document:
    async with async_session() as session:
        document = Document(workspace_id=workspace_id, filename=filename, mime_type="text/plain")
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document


async def verify():
    print("Starting Week 7 Workspace Isolation Verification...")

    primary_workspace = await get_or_create_workspace("Week 7 Primary Workspace", f"wk7-primary-{uuid.uuid4()}")
    secondary_workspace = await get_or_create_workspace("Week 7 Secondary Workspace", f"wk7-secondary-{uuid.uuid4()}")

    primary_document = await create_document(primary_workspace.id, "primary-scope.txt")
    secondary_document = await create_document(secondary_workspace.id, "secondary-scope.txt")

    await QdrantService.init_collection()
    dummy_vector = [0.33] * 1024
    await QdrantService.upsert_chunks(
        str(primary_workspace.id),
        str(primary_document.id),
        ["Primary workspace fact: Atlas belongs only to the primary workspace."],
        [dummy_vector],
    )
    await QdrantService.upsert_chunks(
        str(secondary_workspace.id),
        str(secondary_document.id),
        ["Secondary workspace fact: Borealis belongs only to the secondary workspace."],
        [dummy_vector],
    )

    primary_hits = await QdrantService.search_chunks(str(primary_workspace.id), dummy_vector, limit=10)
    secondary_hits = await QdrantService.search_chunks(str(secondary_workspace.id), dummy_vector, limit=10)

    print(f"Primary workspace hits: {len(primary_hits)}")
    print(f"Secondary workspace hits: {len(secondary_hits)}")

    primary_text_ok = any("primary workspace" in hit["text"].lower() for hit in primary_hits)
    secondary_text_ok = any("secondary workspace" in hit["text"].lower() for hit in secondary_hits)
    cross_text_leak = any("secondary workspace" in hit["text"].lower() for hit in primary_hits)

    async with async_session() as session:
        rejected_cross_scope = False
        try:
            await _validate_document_scope([secondary_document.id], primary_workspace, session)
        except HTTPException:
            rejected_cross_scope = True

    print(f"Primary search returns primary data: {primary_text_ok}")
    print(f"Secondary search returns secondary data: {secondary_text_ok}")
    print(f"Primary search leaked secondary data: {cross_text_leak}")
    print(f"Cross-workspace document scope rejected: {rejected_cross_scope}")

    if not primary_text_ok or not secondary_text_ok or cross_text_leak or not rejected_cross_scope:
        raise RuntimeError("Week 7 workspace isolation verification failed.")


if __name__ == "__main__":
    asyncio.run(verify())
