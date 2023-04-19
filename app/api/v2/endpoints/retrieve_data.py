from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from app.api.v2.endpoints.utils import check_index, order_by_key, order_by_value

from app.db.database import db, get_collection
from app.schemas.data import GetDataResponse

router = APIRouter()


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_model=GetDataResponse,
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

    # Set default result to empty dictionary
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
            if not isinstance(startAt, (str, type(None))) or not isinstance(
                endAt, (str, type(None))
            ):
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail={
                        "error": "Provided key index type is invalid, must be string"
                    },
                )
            collections = order_by_key(collections, startAt, endAt)

        if equalTo:
            if len(collections) > 0:
                collections = [equalTo] if equalTo in collections else []

        if len(collections) > 0:
            for col in collections:
                collection = get_collection(col)
                docs = await collection.find({}, {"_id": 0}).to_list(length=None)

                result[col] = {}
                for doc in docs:
                    result[col].update({doc["_fm_id"]: doc["_fm_val"]})

    elif orderBy == "$value":
        index_ = await check_index()
        if index_ is None or ".value" not in index_:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "error": 'Index not defined, add ".indexOn": ".value", for path "/", to the rules'
                },
            )

        for col in collections:
            collection = get_collection(col)
            docs = await collection.find({}, {"_id": 0}).to_list(length=None)

            if equalTo:
                if docs == equalTo:
                    result[col] = {}
                    for doc in docs:
                        result[col].update({doc["_fm_id"]: doc["_fm_val"]})
            else:
                result[col] = {}
                for doc in docs:
                    result[col].update({doc["_fm_id"]: doc["_fm_val"]})

        result = order_by_value(result, startAt, endAt)

    # Filtering by a specified child key
    elif type(orderBy) is str:
        index_ = await check_index()
        if not index_ or orderBy not in index_:
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
    response_model=GetDataResponse,
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

        sort_order = -1 if limitToLast else 1

        # Ordering by key
        if orderBy == "$key":
            # StartAt & EndAt filters
            if startAt or endAt:
                if not isinstance(startAt, (str, type(None))) or not isinstance(
                    endAt, (str, type(None))
                ):
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail={
                            "error": "Provided key index type is invalid, must be string"
                        },
                    )

                query = {}
                if startAt is not None:
                    query.update({"$gte": startAt})
                if endAt is not None:
                    query.update({"$lte": endAt})
                if query:
                    filter_.update({"_fm_id": query})

            if equalTo:
                filter_.update({"_fm_id": str(equalTo)})

            sort_.append(("_fm_id", sort_order))

        # Ordering by Value
        elif orderBy == "$value":
            index_ = await check_index(path)
            if index_ is None or ".value" not in index_:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail={
                        "error": f'Index not defined, add ".indexOn": ".value", for path "{path}", to the rules'
                    },
                )

            # Filters: startAt and endAt
            query = {}
            if startAt is not None:
                query.update({"$gte": startAt})
            if endAt is not None:
                query.update({"$lte": endAt})
            if query:
                filter_.update({"_fm_val": query})

            if equalTo:
                filter_.update({"_fm_val": equalTo})

            sort_.append(("_fm_val", sort_order))

        # Ordering by child key
        elif type(orderBy) is str:
            index_ = await check_index(path_components[0])
            if index_ is None or orderBy not in index_:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail={
                        "error": f'Index not defined, add ".indexOn": ".value", for path "/{path}", to the rules'
                    },
                )
            orderBy = orderBy.rstrip("/").replace("/", ".")

            # Filters: startAt and endAt
            query = {}
            if startAt is not None:
                query.update({"$gte": startAt})
            if endAt is not None:
                query.update({"$lte": endAt})
            if query:
                filter_.update({f"_fm_val.{orderBy}": query})

            if equalTo:
                filter_.update({f"_fm_val.{orderBy}": equalTo})

            sort_.append((f"_fm_val.{orderBy}", sort_order))

        elif orderBy is None:
            sort_.append(("_fm_id", sort_order))

        # Fetch Data
        docs = collection.find(filter_, project).sort(sort_)

        # Update results Limit
        if limitToFirst or limitToLast:
            docs = docs.limit(limitToFirst or limitToLast)

        # Parse Mongo Documents
        docs = await docs.to_list(length=None)
        result = {}
        for doc in docs:
            result[doc["_fm_id"]] = doc["_fm_val"]
        return result
