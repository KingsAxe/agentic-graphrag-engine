from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.postgres import get_db
from src.models.workspace import Workspace

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_current_workspace(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)  
):
    if not api_key.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    token = api_key.split(" ")[1]
    
    stmt = select(Workspace).where(Workspace.api_key == token)
    result = await db.execute(stmt)
    workspace = result.scalars().first()
    
    if not workspace or not workspace.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key",
        )
    return workspace
