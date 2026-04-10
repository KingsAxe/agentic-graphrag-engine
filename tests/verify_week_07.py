import asyncio
import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.postgres import async_session
from src.models.workspace import Workspace
from src.services.agent.orchestrator import run_agent_with_trace
from src.services.qdrant_service import QdrantService
from sqlalchemy import select


async def get_workspace_id() -> str:
    async with async_session() as session:
        result = await session.execute(select(Workspace).where(Workspace.name == "Dev Test Workspace"))
        workspace = result.scalars().first()
        if not workspace:
            raise RuntimeError("Run create_workspace.py first.")
        return str(workspace.id)


async def seed_scope_test_data(workspace_id: str) -> tuple[str, str]:
    await QdrantService.init_collection()

    document_id_alpha = str(uuid.uuid4())
    document_id_beta = str(uuid.uuid4())

    shared_vector = [0.25] * 1024

    await QdrantService.upsert_chunks(
        workspace_id,
        document_id_alpha,
        ["Alpha dossier: Project Atlas budget is 12 million dollars."],
        [shared_vector],
    )
    await QdrantService.upsert_chunks(
        workspace_id,
        document_id_beta,
        ["Beta dossier: Project Borealis budget is 34 million dollars."],
        [shared_vector],
    )
    return document_id_alpha, document_id_beta


async def verify():
    print("Starting Week 7 Verification...")
    workspace_id = await get_workspace_id()
    document_id_alpha, document_id_beta = await seed_scope_test_data(workspace_id)

    query = "What budget is recorded in the dossier?"

    workspace_result = await run_agent_with_trace(query, workspace_id)
    scoped_alpha_result = await run_agent_with_trace(query, workspace_id, [document_id_alpha])
    scoped_beta_result = await run_agent_with_trace(query, workspace_id, [document_id_beta])

    print("\n--- Workspace Scope Trace ---")
    for item in workspace_result["trace"]:
        print(f"{item['title']}: {item['detail']}")

    print("\n--- Alpha Document Scope Response ---")
    print(scoped_alpha_result["response"])

    print("\n--- Beta Document Scope Response ---")
    print(scoped_beta_result["response"])

    alpha_ok = document_id_alpha in scoped_alpha_result["response"] and document_id_beta not in scoped_alpha_result["response"]
    beta_ok = document_id_beta in scoped_beta_result["response"] and document_id_alpha not in scoped_beta_result["response"]
    trace_ok = any(item["step"] == "retrieval_scope" for item in scoped_alpha_result["trace"])

    print("\n--- Assertions ---")
    print(f"Alpha scope isolated correctly: {alpha_ok}")
    print(f"Beta scope isolated correctly: {beta_ok}")
    print(f"Trace includes retrieval scope: {trace_ok}")

    if not (alpha_ok and beta_ok and trace_ok):
        raise RuntimeError("Week 7 verification failed.")


if __name__ == "__main__":
    asyncio.run(verify())
