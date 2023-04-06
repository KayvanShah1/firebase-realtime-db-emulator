from typing import Optional
from pymongo.collection import Collection
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder


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
    aggregation_query = []

    if path is None:
        filter = {}
        project = {"$project": {"_id": 0}}
        # aggregation_query.append(project)
    else:
        nested_key = get_mongo_style_path(path)

        filter = {"$match": {nested_key: {"$exists": True}}}
        project = {"$project": {"_id": 0, "data": f"${nested_key}"}}
        # aggregation_query.append(project)
        # aggregation_query.append(filter)
        # aggregation_query.append({"$unwind": "$data"})
        # aggregation_query.append({"$replaceRoot": {"newRoot": "$data.v"}})

    # result = await collection.aggregate(aggregation_query).to_list(length=None)
    result = await collection.find_one(filter, project)
    # result = result[0]["data"]

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
                detail={
                    "error": "orderBy must be defined when other query parameters are defined"
                },
            )

        if limitToFirst is not None and limitToLast is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "limitToFirst and limitToLast cannot both be defined"},
            )

    return result
