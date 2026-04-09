import logging
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.services.agent.orchestrator import run_agent_with_trace

router = APIRouter(prefix="/query", tags=["Query"])
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str

@router.post("")
async def execute_query(
    request: QueryRequest,
    workspace: Workspace = Depends(get_current_workspace)
):
    try:
        logger.info("Executing query for workspace %s", workspace.id)
        result = await run_agent_with_trace(request.query, str(workspace.id))
        return {
            "query": request.query,
            "response": result["response"],
            "trace": result["trace"],
            "workspace_id": str(workspace.id)
        }
    except Exception as e:
        logger.exception("Query execution failed for workspace %s", workspace.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def execute_query_stream(
    request: QueryRequest,
    workspace: Workspace = Depends(get_current_workspace)
):
    async def event_stream():
        try:
            logger.info("Streaming query execution for workspace %s", workspace.id)
            result = await run_agent_with_trace(request.query, str(workspace.id))

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
                        "workspace_id": str(workspace.id),
                    },
                }
            ) + "\n"
        except Exception as e:
            logger.exception("Query stream execution failed for workspace %s", workspace.id)
            yield json.dumps({"type": "error", "data": {"detail": str(e)}}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
