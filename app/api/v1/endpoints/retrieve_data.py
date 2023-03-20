import uuid
from typing import Optional
import pymongo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.db.database import get_collection, base_collection

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
    """_summary_

    Args:
        path (str): _description_
        orderBy (Optional[str  |  None], optional): _description_. Defaults to None.
        limitToFirst (Optional[int  |  None], optional): _description_. Defaults to None.
        limitToLast (Optional[int  |  None], optional): _description_. Defaults to None.
        equalTo (Optional[int  |  str  |  None], optional): _description_. Defaults to None.
        startAt (Optional[int  |  str  |  None], optional): _description_. Defaults to None.
        endAt (Optional[int  |  str  |  None], optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    return {"Message": "Done"}


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
    """_summary_

    Args:
        path (str): _description_
        orderBy (Optional[str  |  None], optional): _description_. Defaults to None.
        limitToFirst (Optional[int  |  None], optional): _description_. Defaults to None.
        limitToLast (Optional[int  |  None], optional): _description_. Defaults to None.
        equalTo (Optional[int  |  str  |  None], optional): _description_. Defaults to None.
        startAt (Optional[int  |  str  |  None], optional): _description_. Defaults to None.
        endAt (Optional[int  |  str  |  None], optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    return {"Message": path}
