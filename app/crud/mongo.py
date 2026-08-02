from typing import Optional

from fastapi import HTTPException, status
from pymongo.collection import Collection


def get_mongo_style_path(path):
    """Recreate MongoDB style key"""
    path_components = path.strip("/").split("/")
    nested_key = ".".join(path_components)
    return nested_key


async def get_data(
    path: str = None,
    collection: Collection = None,
    orderBy: Optional[str | None] = None,
    limitToFirst: Optional[int | None] = None,
    limitToLast: Optional[int | None] = None,
    equalTo: Optional[int | str | None] = None,
    startAt: Optional[int | str | None] = None,
    endAt: Optional[int | str | None] = None,
):
    if path is None:
        result = await collection.find_one({}, {"_id": 0})
    else:
        nested_key = get_mongo_style_path(path)
        result = await collection.find_one({nested_key: {"$exists": True}}, {"_id": 0})
        if result is not None:
            for component in path.strip("/").split("/"):
                result = result[component]

    if (
        limitToFirst is not None
        or limitToLast is not None
        or equalTo is not None
        or startAt is not None
        and endAt is not None
    ):
        if orderBy is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "orderBy must be defined when other query parameters are defined"},
            )

        if limitToFirst is not None and limitToLast is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "limitToFirst and limitToLast cannot both be defined"},
            )

    return result
