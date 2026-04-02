from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.services.agent.orchestrator import run_agent

router = APIRouter(prefix="/query", tags=["Query"])

class QueryRequest(BaseModel):
    query: str

@router.post("")
async def execute_query(
    request: QueryRequest,
    workspace: Workspace = Depends(get_current_workspace)
):
    try:
        response = await run_agent(request.query, str(workspace.id))
        return {
            "query": request.query,
            "response": response,
            "workspace_id": str(workspace.id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
