from typing import Any

from fastapi import APIRouter, Body, HTTPException, status

from app.domain.firebase_path import FirebasePath
from app.schemas.data import PostDataResponse
from app.services.v1_data import EmptyV1PayloadError, V1DataService

router = APIRouter()


def empty_payload_error(error: EmptyV1PayloadError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/.json", response_model=PostDataResponse, status_code=status.HTTP_200_OK)
async def push_data_root(data: Any = Body(default=None)) -> dict:
    try:
        generated_id = await V1DataService().push_root(data)
    except EmptyV1PayloadError as error:
        raise empty_payload_error(error) from error
    return {"name": generated_id}


@router.put("/.json", status_code=status.HTTP_200_OK)
async def put_data_root(data: dict | None = Body(default=None)) -> dict:
    try:
        return await V1DataService().put_root(data)
    except EmptyV1PayloadError as error:
        raise empty_payload_error(error) from error


@router.delete("/.json", status_code=status.HTTP_200_OK)
async def delete_data_root() -> None:
    await V1DataService().delete_root()


@router.post(
    "/{path:path}.json",
    response_model=PostDataResponse,
    status_code=status.HTTP_200_OK,
)
async def post_data(path: str, data: Any = Body(default=None)) -> dict:
    try:
        generated_id = await V1DataService().push(FirebasePath.parse(path), data)
    except EmptyV1PayloadError as error:
        raise empty_payload_error(error) from error
    return {"name": generated_id}


@router.put("/{path:path}.json", status_code=status.HTTP_200_OK)
async def put_data(path: str, data: Any = Body(default=None)) -> Any:
    try:
        return await V1DataService().put(FirebasePath.parse(path), data)
    except EmptyV1PayloadError as error:
        raise empty_payload_error(error) from error


@router.patch("/{path:path}.json", status_code=status.HTTP_200_OK)
async def update_data(path: str, data: Any = Body(default=None)) -> Any:
    return await V1DataService().patch(FirebasePath.parse(path), data)


@router.delete("/{path:path}.json", status_code=status.HTTP_200_OK)
async def delete_data(path: str) -> None:
    if not await V1DataService().delete(FirebasePath.parse(path)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key doesn't exist")
