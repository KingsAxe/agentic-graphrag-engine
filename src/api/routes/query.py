import logging
import asyncio
import json
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.services.agent.orchestrator import run_agent_with_trace
from src.models.document import Document
from src.db.postgres import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/query", tags=["Query"])
logger = logging.getLogger(__name__)
INVALID_SCOPE_DETAIL = "One or more document_ids do not belong to the authenticated workspace."

class QueryRequest(BaseModel):
    query: str
    scope: Literal["workspace", "documents"] = "workspace"
    document_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope == "workspace":
            self.document_ids = []
            return self
        if not self.document_ids:
            raise ValueError("document_ids must be provided when scope='documents'")
        return self


async def _validate_document_scope(
    document_ids: list[UUID],
    workspace: Workspace,
    db: AsyncSession,
) -> list[str]:
    scoped_document_ids = list(dict.fromkeys(str(document_id) for document_id in document_ids if document_id))
    if not scoped_document_ids:
        return []

    stmt = select(Document.id).where(
        Document.workspace_id == workspace.id,
        Document.id.in_(scoped_document_ids),
    )
    result = await db.execute(stmt)
    allowed_document_ids = {str(document_id) for document_id in result.scalars().all()}
    invalid_document_ids = sorted(set(scoped_document_ids) - allowed_document_ids)
    if invalid_document_ids:
        logger.warning(
            "Workspace %s requested invalid document scope ids: %s",
            workspace.id,
            invalid_document_ids,
        )
        raise HTTPException(
            status_code=400,
            detail=INVALID_SCOPE_DETAIL,
        )
    return scoped_document_ids

@router.post("")
async def execute_query(
    request: QueryRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    try:
        scoped_document_ids = await _validate_document_scope(request.document_ids, workspace, db)
        logger.info("Executing query for workspace %s", workspace.id)
        result = await run_agent_with_trace(request.query, str(workspace.id), scoped_document_ids)
        return {
            "query": request.query,
            "response": result["response"],
            "trace": result["trace"],
            "scope": request.scope,
            "document_ids": scoped_document_ids,
            "workspace_id": str(workspace.id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Query execution failed for workspace %s", workspace.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def execute_query_stream(
    request: QueryRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    scoped_document_ids = await _validate_document_scope(request.document_ids, workspace, db)

    async def event_stream():
        try:
            logger.info("Streaming query execution for workspace %s", workspace.id)
            result = await run_agent_with_trace(request.query, str(workspace.id), scoped_document_ids)

            for trace in result["trace"]:
                yield json.dumps({"type": "trace", "data": trace}) + "\n"
                await asyncio.sleep(0.05)

            yield json.dumps(
                {
                    "type": "final",
                    "data": {
                        "query": request.query,
                        "response": result["response"],
                        "trace": result["trace"],
                        "scope": request.scope,
                        "document_ids": scoped_document_ids,
                        "workspace_id": str(workspace.id),
                    },
                }
            ) + "\n"
        except Exception as e:
            logger.exception("Query stream execution failed for workspace %s", workspace.id)
            yield json.dumps({"type": "error", "data": {"detail": str(e)}}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
