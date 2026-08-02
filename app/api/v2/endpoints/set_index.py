from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, status

from app.repositories.indexes import IndexRepository

router = APIRouter()


@router.put(
    "/set-index",
    status_code=status.HTTP_200_OK,
    response_description="Successfully set the index for the provided path",
)
async def set_index(
    index_on: Annotated[str | dict | list, Body()] = ".value",
    path: str | None = None,
) -> dict:
    """This route allows users to set an index for a specific path in their MongoDB collection. The user can provide a
    path and an index_on argument that can be either a string, a dictionary, or a list.
    """
    return await IndexRepository().set(path, index_on)


@router.delete(
    "/delete-index",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def delete_index(path: str | None = None) -> None:
    """This route allows users to delete an existing index for a specific path in their MongoDB collection. The user
    can provide a path for which the index needs to be deleted."""

    if not await IndexRepository().delete(path):
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"Index `{IndexRepository.normalize_path(path)}` does not exist",
        )


@router.get(
    "/get-rules",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched Index Rules",
)
async def get_rules() -> dict:
    return await IndexRepository().list_rules()
