import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logging import setup_logging
from src.core.readiness import get_launch_readiness
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.api.routes import documents, query

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(query.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def log_startup_state():
    readiness = get_launch_readiness()
    logger.info("Application startup readiness: %s", readiness)

@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "readiness": get_launch_readiness(),
    }

@app.get(f"{settings.API_V1_STR}/secure-test")
async def secure_endpoint_test(workspace: Workspace = Depends(get_current_workspace)):
    return {"message": "Authenticated as workspace", "workspace_id": str(workspace.id)}
