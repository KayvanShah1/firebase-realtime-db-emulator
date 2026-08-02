from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_query_spec
from app.domain.firebase_path import FirebasePath
from app.domain.query import QuerySpec
from app.services.v1_data import V1DataService

router = APIRouter()


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully fetched data",
)
async def query_data_root(
    query: Annotated[QuerySpec, Depends(get_query_spec)],
) -> Any:
    return await V1DataService().get()


@router.get(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully fetched data",
)
async def query_data(
    query: Annotated[QuerySpec, Depends(get_query_spec)],
    path: str,
) -> Any:
    return await V1DataService().get(FirebasePath.parse(path))
