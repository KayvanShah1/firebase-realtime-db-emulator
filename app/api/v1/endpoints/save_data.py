import uuid
from typing import Optional
import pymongo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.db.database import get_collection, base_collection

router = APIRouter()


@router.get(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def query_data(
    path: str,
    orderBy: Optional[str],
    limitToFirst: Optional[int],
    limitToLast: Optional[int],
    equalTo: Optional[int | str],
    startAt: Optional[int | str],
    endAt: Optional[int | str],
):
    return {"Message": path}
