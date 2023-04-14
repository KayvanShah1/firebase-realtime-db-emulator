from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.encoders import jsonable_encoder
from app.api.v2.endpoints.utils import check_index, get_items_between_indexes

from app.db.database import db, get_collection

router = APIRouter()


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def query_data_root_v2(
    orderBy: Annotated[str | None, Query()] = None,
    limitToFirst: Annotated[int | None, Query()] = None,
    limitToLast: Annotated[int | None, Query()] = None,
    equalTo: Annotated[int | str | None, Query()] = None,
    startAt: Annotated[int | str | None, Query()] = None,
    endAt: Annotated[int | str | None, Query()] = None,
) -> dict | None:
    # Parameter validation and checks for violations
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

    result = {}

    collections = await db.list_collection_names()
    # Filter out special collection names
    collections = [i for i in collections if i not in ["__fm_root__", "__fm_rules__"]]
    collections.sort()

    # Limit Querying and Filtering
    if limitToFirst:
        collections = collections[:limitToFirst]
    if limitToLast:
        collections = collections[-limitToLast:]

    # Sorting and ordering of JSON documents
    if orderBy == "$key":
        # StartAt & EndAt filters
        if startAt or endAt:
            collections = get_items_between_indexes(collections, startAt, endAt)

        if equalTo:
            if len(collections) > 0:
                if equalTo in collections:
                    collections = [equalTo]

        if len(collections) > 0:
            for col in collections:
                collection = get_collection(col)
                docs = await collection.find({}, {"_id": 0}).to_list(length=None)

                result[col] = {}
                for doc in docs:
                    result[col].update({doc["_fm_id"]: doc["_fm_val"]})

    elif orderBy == "$value":
        index_ = await check_index("__root__")
        if index_ is None:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "error": 'Index not defined, add ".indexOn": ".value", for path "/", to the rules'
                },
            )
        # if index_ == ".value" or ".value" in index_:
        #     {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}

    # Filtering by a specified child key
    elif type(orderBy) is str:
        index_ = await check_index()
        if not index_:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "error": f'Index not defined, add ".indexOn": "{orderBy}", for path "/", to the rules'
                },
            )
    # No filter
    else:
        for col in collections:
            collection = get_collection(col)
            docs = await collection.find({}, {"_id": 0}).to_list(length=None)

            result[col] = {}
            for doc in docs:
                result[col].update({doc["_fm_id"]: doc["_fm_val"]})

    return result


@router.get(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully fetched data",
)
async def query_data_v2(
    path: str = Path(description="Enter the path to retrieve data"),
    orderBy: Annotated[str | None, Query()] = None,
    limitToFirst: Annotated[int | None, Query()] = None,
    limitToLast: Annotated[int | None, Query()] = None,
    equalTo: Annotated[int | str | None, Query()] = None,
    startAt: Annotated[int | str | None, Query()] = None,
    endAt: Annotated[int | str | None, Query()] = None,
):
    # Parameter validation and checks for violations
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

    # Recreate MongoDB style key
    path_components = path.strip("/").split("/")
    # Collection name
    collection = get_collection(path_components[0])

    # Fetching data within a document
    if len(path_components) > 1:
        _fm_id = path_components[1]
        nested_components = path_components[2:]

        key = ".".join(nested_components)
        nested_key = f"_fm_val.{key}".strip(".")

        existing_data = await collection.find_one(
            {"_fm_id": _fm_id, nested_key: {"$exists": True}}
        )
        if existing_data is not None:
            existing_data = existing_data["_fm_val"]
            for k in nested_components:
                if type(existing_data) is list:
                    existing_data = existing_data[int(k)]
                else:
                    existing_data = existing_data[k]
            return existing_data
        else:
            return None

    # Fetching data from the entire collection
    else:
        # Query Builder
        filter_ = {}
        project = {"_id": 0}
        sort_ = []

        if orderBy == "$key":
            sort_.append(("_fm_id", 1))
        elif orderBy == "$value":
            ...
        elif type(orderBy) is str:
            ...
        else:
            sort_.append(("_fm_id", 1))

        # Fetch & Parse Mongo Documents
        docs = await collection.find(filter_, project).sort(sort_).to_list(length=None)
        result = {}
        for doc in docs:
            result[doc["_fm_id"]] = doc["_fm_val"]
        return result
