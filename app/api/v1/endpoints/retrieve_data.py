import uuid
from typing import Optional
import pymongo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.db.database import get_collection, base_collection
from app.crud.mongo import get_data

router = APIRouter()


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def query_data_root(
    orderBy: Optional[str | None] = None,
    limitToFirst: Optional[int | None] = None,
    limitToLast: Optional[int | None] = None,
    equalTo: Optional[int | str | None] = None,
    startAt: Optional[int | str | None] = None,
    endAt: Optional[int | str | None] = None,
):
    # collection = get_collection()
    collection = base_collection
    result = await get_data(
        path=None,
        collection=collection,
        orderBy=orderBy,
        limitToFirst=limitToFirst,
        limitToLast=limitToLast,
        equalTo=equalTo,
        startAt=startAt,
        endAt=endAt,
    )
    return result


@router.get(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def query_data(
    path: str,
    orderBy: Optional[str | None] = None,
    limitToFirst: Optional[int | None] = None,
    limitToLast: Optional[int | None] = None,
    equalTo: Optional[int | str | None] = None,
    startAt: Optional[int | str | None] = None,
    endAt: Optional[int | str | None] = None,
):
    # collection = get_collection()
    collection = base_collection
    result = await get_data(
        path=path,
        collection=collection,
        orderBy=orderBy,
        limitToFirst=limitToFirst,
        limitToLast=limitToLast,
        equalTo=equalTo,
        startAt=startAt,
        endAt=endAt,
    )
    return result
