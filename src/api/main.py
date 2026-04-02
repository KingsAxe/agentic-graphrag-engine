from fastapi import FastAPI, Depends
from src.core.config import settings
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.api.routes import documents, query

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(query.router, prefix=settings.API_V1_STR)

@app.get("/")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

@app.get(f"{settings.API_V1_STR}/secure-test")
async def secure_endpoint_test(workspace: Workspace = Depends(get_current_workspace)):
    return {"message": "Authenticated as workspace", "workspace_id": str(workspace.id)}
