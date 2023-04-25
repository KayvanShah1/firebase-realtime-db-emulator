from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from app.api.v2.endpoints.utils import check_index, order_by_key, order_by_value

from app.db.database import db, get_collection
from app.schemas.data import GetDataResponse

router = APIRouter()


@router.get(
    "/.json",
    status_code=status.HTTP_200_OK,
    # response_model=GetDataResponse,
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
    """This API endpoint fetches data from a MongoDB database based on various query parameters.

    Parameters:

        - orderBy (optional): A string indicating the key to use for sorting the results.
        - limitToFirst (optional): An integer indicating the number of records to return from the beginning of the
            collection.
        - limitToLast (optional): An integer indicating the number of records to return from the end of the collection.
        - equalTo (optional): A value used to filter the results. Only records with a matching value are returned.
        - startAt (optional): A value used to filter the results. Only records with a key greater than or equal to
            the specified value are returned.
        - endAt (optional): A value used to filter the results. Only records with a key less than or equal to the
            specified value are returned.

    Returns:

        - A dictionary containing the requested data. The keys are the names of the collections, and the values are
        dictionaries containing the records in the collection.

    Raises:

        - HTTPException with status code 400: If orderBy is not defined when other query parameters are defined, or if
            both limitToFirst and limitToLast are defined.
        - HTTPException with status code 200: If the provided key index type is invalid.
        - HTTPException with status code 200: If the index is not defined.
    """
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
    # if limitToFirst is not None:
    #     collections = collections[:limitToFirst]
    # if limitToLast is not None:
    #     collections = collections[-limitToLast:]

    # Sorting and ordering of JSON documents
    if orderBy == '"$key"':
        # StartAt & EndAt filters
        if startAt is not None or endAt is not None:
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

        if equalTo is not None:
            if len(collections) > 0:
                collections = [equalTo] if equalTo in collections else []

        # Limit Querying and Filtering
        if limitToFirst is not None:
            collections = collections[:limitToFirst]
        if limitToLast is not None:
            collections = collections[-limitToLast:]

        if len(collections) > 0:
            for col in collections:
                collection = get_collection(col)
                docs = await collection.find({}, {"_id": 0}).to_list(length=None)

                result[col] = {}
                for doc in docs:
                    result[col].update({doc["_fm_id"]: doc["_fm_val"]})

    elif orderBy == '"$value"':
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

            if equalTo is not None:
                if docs == equalTo:
                    result[col] = {}
                    for doc in docs:
                        result[col].update({doc["_fm_id"]: doc["_fm_val"]})
            else:
                result[col] = {}
                for doc in docs:
                    result[col].update({doc["_fm_id"]: doc["_fm_val"]})

        result = order_by_value(result, startAt, endAt)

        # Limit Querying and Filtering
        if limitToFirst is not None or limitToLast is not None:
            result = [(k, v) for k, v in result.items()]
            if limitToFirst is not None:
                result = result[:limitToFirst]
            if limitToLast is not None:
                result = result[-limitToLast:]
            result = {k: v for k, v in result}

    # Filtering by a specified child key
    elif type(orderBy) is str:
        if orderBy.startswith('"') and orderBy.endswith('"'):
            orderBy = orderBy.strip('"')
        index_ = await check_index()
        if not index_ or orderBy not in index_:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "error": f'Index not defined, add ".indexOn": "{orderBy}", for path "/", to the rules'
                },
            )

        if startAt is not None or endAt is not None or equalTo is not None:
            collections = []

        # Limit Querying and Filtering
        if limitToFirst is not None:
            collections = collections[:limitToFirst]
        if limitToLast is not None:
            collections = collections[-limitToLast:]

        if len(collections) > 0:
            for col in collections:
                collection = get_collection(col)
                docs = await collection.find({}, {"_id": 0}).to_list(length=None)

                result[col] = {}
                for doc in docs:
                    result[col].update({doc["_fm_id"]: doc["_fm_val"]})
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
    # response_model=GetDataResponse,
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
    """Retrieve data from the specified path of the MongoDB collection.

    Parameters:

        - path (str): The path to retrieve data from.
        - orderBy (str): The key to order the data by.
        - limitToFirst (int): The maximum number of items to retrieve from the beginning of the ordered data.
        - limitToLast (int): The maximum number of items to retrieve from the end of the ordered data.
        - equalTo (str): The value that the ordered data must match.
        - startAt (str): The key to start retrieving data from.
        - endAt (str): The key to stop retrieving data from.

    Returns:

        - GetDataResponse: A dictionary containing the retrieved data.

    Raises:

        - HTTPException 400 Bad Request: If the query parameters violate validation rules.
        - HTTPException: If the orderBy parameter is not defined when other query parameters are defined.
        - HTTPException: If both limitToFirst and limitToLast are defined.
        - HTTPException: If the provided key index type is invalid and it's used to startAt or endAt filters.
    """
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

            # Order by Key
            if orderBy == '"$key"':
                if type(existing_data) is list:
                    if startAt is not None:
                        existing_data = existing_data[int(startAt) :]
                    if endAt is not None:
                        existing_data = existing_data[: int(endAt)]

                    if equalTo is not None:
                        existing_data = (
                            existing_data[int(equalTo)]
                            if int(equalTo) <= len(existing_data)
                            else None
                        )

                    # Limit Querying and Filtering
                    if limitToFirst is not None:
                        existing_data = existing_data[:limitToFirst]
                    if limitToLast is not None:
                        existing_data = existing_data[-limitToLast:]

                elif type(existing_data) is dict:
                    existing_data = sorted(
                        existing_data.items(), key=lambda item: str(item[0])
                    )

                    if startAt is not None:
                        existing_data = [
                            (k, v) for k, v in existing_data if str(k) >= str(startAt)
                        ]
                    if endAt is not None:
                        existing_data = [
                            (k, v) for k, v in existing_data if str(k) <= str(endAt)
                        ]

                    if equalTo is not None:
                        existing_data = (
                            (k, v) for k, v in existing_data if str(k) == equalTo
                        )

                    # Limit Querying and Filtering
                    if limitToFirst is not None:
                        existing_data = existing_data[:limitToFirst]
                    if limitToLast is not None:
                        existing_data = existing_data[-limitToLast:]

                    existing_data = {k: v for k, v in existing_data}

                else:
                    if startAt is not None or endAt is not None or equalTo is not None:
                        existing_data = {}
                    if limitToFirst is not None or limitToLast is not None:
                        existing_data = None
                    else:
                        existing_data = existing_data

            # Ordering by Value
            elif orderBy == '"$value"':
                index_ = await check_index(path)
                if index_ is None or ".value" not in index_:
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail={
                            "error": f'Index not defined, add ".indexOn": ".value", for path "/{path}", to the rules'
                        },
                    )

                if type(existing_data) is list:
                    if startAt is not None:
                        existing_data = [
                            item for item in existing_data if str(item) >= str(startAt)
                        ]
                    if endAt is not None:
                        existing_data = [
                            item for item in existing_data if str(item) <= str(endAt)
                        ]

                    if equalTo is not None:
                        existing_data = [
                            item for item in existing_data if str(item) == str(equalTo)
                        ]

                    # Limit Querying and Filtering
                    if limitToFirst is not None:
                        existing_data = existing_data[:limitToFirst]
                    if limitToLast is not None:
                        existing_data = existing_data[-limitToLast:]

                elif type(existing_data) is dict:
                    existing_data = order_by_value(existing_data, startAt, endAt)
                    existing_data = existing_data.items()

                    if equalTo is not None:
                        existing_data = (
                            (k, v) for k, v in existing_data if str(k) == equalTo
                        )

                    # Limit Querying and Filtering
                    if limitToFirst is not None:
                        existing_data = existing_data[:limitToFirst]
                    if limitToLast is not None:
                        existing_data = existing_data[-limitToLast:]

                    existing_data = {k: v for k, v in existing_data}

                else:
                    if startAt is not None or endAt is not None or equalTo is not None:
                        existing_data = {}
                    if limitToFirst is not None or limitToLast is not None:
                        existing_data = None
                    else:
                        existing_data = existing_data

            # Ordering by child key
            elif type(orderBy) is str:
                if orderBy.startswith('"') and orderBy.endswith('"'):
                    orderBy = orderBy.strip('"')
                index_ = await check_index(path)
                if index_ is None or orderBy not in index_:
                    raise HTTPException(
                        status_code=status.HTTP_200_OK,
                        detail={
                            "error": f'Index not defined, add ".indexOn": "{orderBy}", for path "/{path}", to the rules'
                        },
                    )
                ...

            return existing_data
        else:
            return None

    # Fetching data from the entire collection
    else:
        # Query Builder
        filter_ = {}
        project = {"_id": 0}
        sort_ = []

        sort_order = -1 if limitToLast is not None else 1

        # Ordering by key
        if orderBy == '"$key"':
            # StartAt & EndAt filters
            if startAt is not None or endAt is not None:
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
        elif orderBy == '"$value"':
            index_ = await check_index(path)
            if index_ is None or ".value" not in index_:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail={
                        "error": f'Index not defined, add ".indexOn": ".value", for path "/{path}", to the rules'
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
            if orderBy.startswith('"') and orderBy.endswith('"'):
                orderBy = orderBy.strip('"')
            index_ = await check_index(path_components[0])
            if index_ is None or orderBy not in index_:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail={
                        "error": f'Index not defined, add ".indexOn": "{orderBy}", for path "/{path}", to the rules'
                    },
                )
            orderBy = orderBy.rstrip("/").replace("/", ".")

            # Filters: startAt and endAt
            query = {"$exists": True}
            if startAt is not None:
                query.update({"$gte": startAt})
            if endAt is not None:
                query.update({"$lte": endAt})

            filter_.update({f"_fm_val.{orderBy}": query})

            if equalTo:
                filter_.update({f"_fm_val.{orderBy}": equalTo})

            sort_.append((f"_fm_val.{orderBy}", sort_order))

        elif orderBy is None:
            sort_.append(("_fm_id", sort_order))

        # Fetch Data
        docs = collection.find(filter_, project).sort(sort_)

        # Update results Limit
        if limitToFirst is not None or limitToLast is not None:
            docs = docs.limit(limitToFirst or limitToLast)

        # Parse Mongo Documents
        docs = await docs.to_list(length=None)
        result = {}
        for doc in docs:
            result[doc["_fm_id"]] = doc["_fm_val"]
        return result
