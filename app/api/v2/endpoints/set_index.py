from fastapi import APIRouter, HTTPException, status

from app.db.database import get_collection

router = APIRouter()


@router.put(
    "/set-index",
    status_code=status.HTTP_200_OK,
    response_description="Successfully set the index for the provided path",
)
async def set_index(
    path: str = None, index_on: str | dict | list = ".value"
) -> dict | None:
    """This route allows users to set an index for a specific path in their MongoDB collection. The user can provide a
    path and an index_on argument that can be either a string, a dictionary, or a list.
    """
    if path is None:
        path = "__root__"

    index_collection = get_collection("__fm_rules__")

    index_doc = await index_collection.find_one({"path": path})
    if index_doc is not None:
        _id = index_doc["_id"]

        # Update existing sub-document
        new_data = await index_collection.update_one(
            {"_id": _id, "path": path},
            {"$set": {"indexOn": index_on}},
            upsert=True,
        )
        # Validate the upserted data
        if (
            new_data.modified_count > 0
            or new_data.matched_count > 0
            or new_data.upserted_id
        ):
            valid = True
    else:
        new_index = await index_collection.insert_one(
            {"path": path, "indexOn": index_on}
        )
        valid = await index_collection.find_one(
            {"_id": new_index.inserted_id}, {"_id": 0}
        )

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    return {"path": path, "indexOn": index_on}


@router.delete(
    "/delete-index",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def delete_index(path: str = None) -> None:
    """This route allows users to delete an existing index for a specific path in their MongoDB collection. The user
    can provide a path for which the index needs to be deleted."""

    if path is None:
        path = "__root__"

    index_collection = get_collection("__fm_rules__")

    index_doc = await index_collection.find_one({"path": path})
    if index_doc is not None:
        _id = index_doc["_id"]
        await index_collection.delete_one({"_id": _id})
    else:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"Index `{path}` does not exist",
        )

    return None
