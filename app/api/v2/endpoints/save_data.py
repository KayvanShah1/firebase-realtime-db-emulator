from typing import Any

from fastapi import APIRouter, Body, HTTPException, Path, status

from app.domain.firebase_path import FirebasePath
from app.schemas.data import PostDataResponse
from app.services.v2_data import V2DataService

router = APIRouter()


@router.post(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Successfully created data document",
)
async def post_data_root_v2(data: dict = Body()) -> dict:
    generated_id = await V2DataService().push_root(data)
    return {"name": generated_id}


@router.put(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully replaced root data",
)
async def put_data_root_v2(data: dict[str, dict] = Body()) -> dict:
    return await V2DataService().put_root(data)


@router.delete(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully deleted data",
)
async def delete_data_root_v2() -> None:
    await V2DataService().delete_root()


@router.post(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Successfully created data document",
)
async def post_data_v2(path: str, data: Any = Body()) -> dict:
    generated_id = await V2DataService().push(FirebasePath.parse(path), data)
    return {"name": generated_id}


@router.put(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully replaced data",
)
async def put_data_v2(
    path: str,
    data: dict | int | float | str | list | bool = Body(),
) -> int | float | str | list | dict | bool:
    try:
        return await V2DataService().put(FirebasePath.parse(path), data)
    except TypeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only documents with data type 'dict' and 'list' are allowed",
        ) from error


@router.patch(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully updated data",
)
async def update_data_v2(
    data: dict = Body(),
    path: str = Path(description="Enter the path to update data"),
) -> dict:
    return await V2DataService().patch(FirebasePath.parse(path), data)


@router.delete(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Successfully deleted data",
)
async def delete_data_v2(path: str = Path(description="Enter the path to remove data")) -> None:
    await V2DataService().delete(FirebasePath.parse(path))
