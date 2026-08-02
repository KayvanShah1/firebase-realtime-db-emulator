from fastapi import APIRouter, status

from app.api.v1.endpoints.utils import replace_prefix
from app.crud.mongo import get_data
from app.db.database import get_base_collection

router = APIRouter()


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def query_data_root(
    orderBy: str | None = None,
    limitToFirst: int | None = None,
    limitToLast: int | None = None,
    equalTo: int | str | None = None,
    startAt: int | str | None = None,
    endAt: int | str | None = None,
):
    # collection = get_collection()
    collection = get_base_collection()
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
    orderBy: str | None = None,
    limitToFirst: int | None = None,
    limitToLast: int | None = None,
    equalTo: int | str | None = None,
    startAt: int | str | None = None,
    endAt: int | str | None = None,
):
    # collection = get_collection()
    path = replace_prefix(path)
    collection = get_base_collection()
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
