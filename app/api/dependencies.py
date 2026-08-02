from typing import Annotated

from fastapi import HTTPException, Query, status

from app.domain.query import QuerySpec


def get_query_spec(
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    limit_to_first: Annotated[int | None, Query(alias="limitToFirst", ge=0)] = None,
    limit_to_last: Annotated[int | None, Query(alias="limitToLast", ge=0)] = None,
    equal_to: Annotated[str | None, Query(alias="equalTo")] = None,
    start_at: Annotated[str | None, Query(alias="startAt")] = None,
    end_at: Annotated[str | None, Query(alias="endAt")] = None,
) -> QuerySpec:
    query = QuerySpec(
        order_by=order_by,
        limit_to_first=limit_to_first,
        limit_to_last=limit_to_last,
        equal_to=equal_to,
        start_at=start_at,
        end_at=end_at,
    )
    if error := query.validation_error():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error},
        )
    return query
