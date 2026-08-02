from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from pymongo.errors import PyMongoError

from app.db.database import get_database

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    database: Literal["connected"]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report readiness only after MongoDB accepts a ping command."""
    try:
        result = await get_database().command("ping")
        if result.get("ok") != 1:
            raise RuntimeError("MongoDB ping did not succeed")
    except (PyMongoError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": "unavailable"},
        ) from error

    return HealthResponse(status="healthy", database="connected")
