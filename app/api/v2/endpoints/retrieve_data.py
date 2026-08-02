from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies import get_query_spec
from app.domain.firebase_path import FirebasePath
from app.domain.query import QuerySpec
from app.services.v2_query import QueryRuleError, V2QueryService

router = APIRouter()


def query_rule_error(error: QueryRuleError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_200_OK,
        detail={"error": str(error)},
    )


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully fetched data",
)
async def query_data_root_v2(
    query: Annotated[QuerySpec, Depends(get_query_spec)],
) -> dict | None:
    try:
        return await V2QueryService().get_root(query)
    except QueryRuleError as error:
        raise query_rule_error(error) from error


@router.get(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully fetched data",
)
async def query_data_v2(
    query: Annotated[QuerySpec, Depends(get_query_spec)],
    path: str = Path(description="Enter the path to retrieve data"),
) -> Any:
    try:
        return await V2QueryService().get(FirebasePath.parse(path), query)
    except QueryRuleError as error:
        raise query_rule_error(error) from error
