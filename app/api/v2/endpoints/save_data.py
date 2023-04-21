import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Path, status

from app.api.v2.endpoints.utils import (
    _check_data_type_for_root,
    _check_empty_payload,
    unwrap_path_to_dict,
)
from app.db.database import db, get_collection
from app.schemas.data import PostDataResponse

router = APIRouter()


@router.post(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data_root_v2(
    data: dict = {"user101": {"first_name": "John", "last_name": "Wick"}}
) -> dict:
    """
    Create a new data document.

    Parameters:

        - `data`: a dictionary of data to be inserted.

    Returns:

        - A dictionary containing the unique ID of the created document.

    Raises:

        - `HTTPException`: if the payload is empty or there is an error creating the document.
    """
    _check_empty_payload(data)

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    collection = get_collection(id)
    await collection.create_index("_fm_id", unique=True, name="_fm_id_")

    valid = True
    # Create and Insert the documents
    docs = [{"_fm_id": k, "_fm_val": v} for k, v in data.items()]
    result = await collection.insert_many(docs, ordered=False)

    # Validate the insertion
    if len(result.inserted_ids) != len(docs):
        valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return {"name": id}


@router.put(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully created data document",
)
async def put_data_root_v2(
    data: dict = {
        "dummy": {"type": "string", "value": "arbitary"},
        "examples": {"type": "string", "value": "arbitary"},
    }
) -> dict:
    """
    Create or update documents in the root collection.

    Args:

        - data (dict): A dictionary containing the documents to create or update. Each
            document should be represented as a key-value pair, where the key is the
            document ID and the value is a dictionary containing the document's data.

    Returns:

        - dict: The original data submitted to the endpoint.

    Raises:

        - HTTPException: If the payload is empty or if there was an error during
        insertion.
    """

    _check_empty_payload(data)
    og_data = data
    valid = True

    for key, val in data.items():
        # Find and drop old collection with same names
        collection = get_collection(key)
        await collection.drop()
        await collection.create_index("_fm_id", unique=True, name="_fm_id_")

        # Validate and prepare the documents
        _check_data_type_for_root(val)
        docs = [{"_fm_id": k, "_fm_val": v} for k, v in val.items()]
        # Insert the documents
        result = await collection.insert_many(docs, ordered=False)

        # Validate the insertion
        if len(result.inserted_ids) != len(docs):
            valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return og_data


@router.delete(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully deleted data",
)
async def delete_data_root_v2() -> None:
    """
    Deletes all collections in the database.

    Returns:

        - None: if all collections were deleted successfully.

    Raises:

        - None: this function does not raise any exceptions.
    """
    collections = await db.list_collection_names()
    for col in collections:
        await get_collection(col).drop()
    return None


@router.post(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data_v2(path: str, data: dict | Any = None) -> dict:
    # Recreate MongoDB style key
    path_components = path.strip("/").split("/")
    collection = get_collection(path_components[0])

    # Create a new ID for data to insert
    random_id = uuid.uuid4().hex

    if data is None:
        return {"name": random_id}

    # Overwrite existing data at a key path
    if len(path_components) > 1:
        _fm_id = path_components[1]
        parent_components = path_components[2:-1]
        child_components = path_components[2:]

        nested_key = ".".join(child_components)
        parent_key = ".".join(parent_components)

        if len(parent_components) != 0:
            parent_key = nested_key
        nested_key = f"_fm_val.{nested_key}".strip(".")
        parent_key = f"_fm_val.{parent_key}".strip(".")

        existing_data = await collection.find_one(
            {"_fm_id": _fm_id, parent_key: {"$exists": True}}
        )
        if existing_data is not None:
            _id = existing_data["_id"]

            # Update existing sub-document
            new_data = await collection.update_one(
                {"_id": _id, "_fm_id": _fm_id},
                {"$set": {f"{nested_key}.{random_id}": data}},
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
            # Traverse over the path components
            for key in path_components[:1:-1]:
                data = {key: data}
            # Push Data
            new_data = await collection.insert_one(
                {"_fm_id": random_id, "_fm_val": data}
            )
            # Validation
            valid = await collection.find_one({"_id": new_data.inserted_id}, {"_id": 0})

    # Pushing data at a collection level
    else:
        try:
            await collection.create_index("_fm_id", unique=True, name="_fm_id_")
        except Exception as e:
            pass
        # Push Data
        result = await collection.insert_one({"_fm_id": random_id, "_fm_val": data})
        # Validation
        valid = await collection.find_one({"_id": result.inserted_id}, {"_id": 0})

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return {"name": random_id}


@router.put(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully created data document",
)
async def put_data_v2(
    path: str, data: dict | int | float | str | list | bool = None
) -> int | float | str | list | dict | bool:
    """
    Create or update a document at the given path in MongoDB collection.

    Params:

        - path: str
        The path to the MongoDB collection or sub-document.

        - data: dict | Any, optional (default=None)
        The data to be added or updated. If not provided, a new document will be created
        with a randomly generated id.

    Returns:

        - dict
            A dictionary containing the name of the newly created or updated document.

    Raises:

        - HTTPException
            If there is an internal server error during document creation or update.
    """
    _check_empty_payload(data)
    valid = True
    og_data = data

    # Recreate MongoDB style key
    path_components = path.strip("/").split("/")
    # Collection name
    collection = get_collection(path_components[0])

    # Overwrite existing data at a key path
    if len(path_components) > 1:
        _fm_id = path_components[1]
        # if _fm_id.isdigit():
        #     _fm_id = int(_fm_id)
        parent_components = path_components[2:-1]
        child_components = path_components[2:]

        nested_key = ".".join(child_components)
        parent_key = ".".join(parent_components)

        if len(parent_components) != 0:
            parent_key = nested_key
        nested_key = f"_fm_val.{nested_key}".strip(".")
        parent_key = f"_fm_val.{parent_key}".strip(".")

        existing_data = await collection.find_one(
            {"_fm_id": _fm_id, parent_key: {"$exists": True}}
        )
        if existing_data is not None:
            _id = existing_data["_id"]

            # Update existing sub-document
            new_data = await collection.update_one(
                {"_id": _id, "_fm_id": _fm_id},
                {"$set": {nested_key: data}},
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
            # Traverse over the path components
            for key in path_components[:1:-1]:
                data = {key: data}
            # Push Data
            new_data = await collection.insert_one({"_fm_id": _fm_id, "_fm_val": data})
            # Validation
            valid = await collection.find_one({"_id": new_data.inserted_id}, {"_id": 0})

    # Pushing data at a collection level
    else:
        await collection.drop()
        await collection.create_index("_fm_id", unique=True, name="_fm_id_")
        if type(data) is list:
            docs = [{"_fm_id": str(k), "_fm_val": v} for k, v in enumerate(data)]
        elif type(data) is dict:
            docs = [{"_fm_id": k, "_fm_val": v} for k, v in data.items()]
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only documents with data type 'dict' and 'list' are allowed",
            )
        # Insert the documents
        result = await collection.insert_many(docs, ordered=False)

        # Validate the insertion
        if len(result.inserted_ids) != len(docs):
            valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return og_data


@router.patch(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully updated data",
)
async def update_data_v2(
    path: str = Path(description="Enter the path to update data"),
    data: dict = {"key": "value"},
) -> dict:
    """Updates data in a collection or a specific document.

    Params:

        - path (str): The path to the document to be updated in the collection.
            Defaults to None.
        - data (dict): The data to be updated in the document. Defaults to
            {"key": "value"}.

    Returns:

        - dict: The updated data.

    Raises:

        - HTTPException: If the update fails.
    """
    valid = True
    # Create a copy of data
    og_data = data

    path_components = path.strip("/").split("/")
    collection = get_collection(path_components[0])

    # Updating data at a key path
    if len(path_components) > 1:
        # Recreate MongoDB style key
        _fm_id = path_components[1]
        # if _fm_id.isdigit():
        #     _fm_id = int(_fm_id)
        parent_components = path_components[2:-1]
        child_components = path_components[2:]

        nested_key = ".".join(child_components)
        parent_key = ".".join(parent_components)

        if len(parent_components) != 0:
            parent_key = nested_key
        nested_key = f"_fm_val.{nested_key}".strip(".")
        parent_key = f"_fm_val.{parent_key}".strip(".")

        existing_data = await collection.find_one(
            {"_fm_id": _fm_id, parent_key: {"$exists": True}}
        )
        if existing_data is not None:
            _id = existing_data["_id"]

            setter = {f"{nested_key}.{k.replace('/','.')}": v for k, v in data.items()}
            # Update or upsert the data
            new_data = await collection.update_one(
                {"_id": _id}, {"$set": setter}, upsert=True
            )
            # Validate the upserted data
            if (
                new_data.modified_count > 0
                or new_data.matched_count > 0
                or new_data.upserted_id
            ):
                valid = True

        else:
            # Traverse over the path components
            for key in path_components[:1:-1]:
                data = {key: data}

            # Push Data
            data = unwrap_path_to_dict(data) if type(data) is dict else data
            new_data = await collection.insert_one({"_fm_id": _fm_id, "_fm_val": data})
            # Validation
            valid = await collection.find_one({"_id": new_data.inserted_id}, {"_id": 0})

    # Pushing data at a collection level
    else:
        # Upserting existing data
        _is_path_in_key = [True if "/" in k else False for k in data.keys()]
        if True in _is_path_in_key:
            for k, v in data.items():
                key_components = k.strip("/").split("/")
                _fm_id = key_components[0]

                if len(key_components) > 1:
                    nested_key = ".".join(key_components[1:])
                    update_key = f"_fm_val.{nested_key}".strip(".")

                    setter = {update_key: v}
                else:
                    if type(v) is dict:
                        setter = {f"_fm_val.{k}": _v for k, _v in v.items()}
                    else:
                        setter = {"_fm_val": v}
                # Update or upsert the data
                await collection.update_one(
                    {"_fm_id": _fm_id}, {"$set": setter}, upsert=True
                )

        # Upserting new or old data
        else:
            docs = [
                {
                    "_fm_id": k,
                    "_fm_val": unwrap_path_to_dict(v) if type(v) is dict else v,
                }
                for k, v in data.items()
            ]
            for doc in docs:
                await collection.update_one(
                    {"_fm_id": doc["_fm_id"]},
                    {"$set": {"_fm_val": doc["_fm_val"]}},
                    upsert=True,
                )

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return og_data


@router.delete(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully deleted",
)
async def delete_data_v2(path: str = Path(description="Enter the path to remove data")):
    """This is an API endpoint for deleting data from a specified Firebase database reference.
    The endpoint is a HTTP DELETE request with a URL parameter 'path' which is the path to the
    data that needs to be removed.

    Parameters:

        - path (str): the path to the data that needs to be removed. This is a required parameter.

    Response:

        - None: If the data is successfully deleted, the endpoint returns None.
        - HTTP Response Status Code:
            - 200 OK: The endpoint returns a 200 status code if the data is successfully deleted.

    Exceptions:

        - HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR): If an internal server
        error occurs, the endpoint raises an HTTPException with a 500 status code and the detail
        message "Internal Server Error".
    """
    valid = False
    path_components = path.strip("/").split("/")

    # Check if collection exists
    if path_components[0] in await db.list_collection_names():
        collection = get_collection(path_components[0])

        if len(path_components) > 1:
            # Recreate MongoDB style key
            _fm_id = path_components[1]
            # if _fm_id.isdigit():
            #     _fm_id = int(_fm_id)
            child_components = path_components[2:]
            nested_key = ".".join(child_components)
            nested_key = f"_fm_val.{nested_key}".strip(".")

            existing_data = await collection.find_one(
                {"_fm_id": _fm_id, nested_key: {"$exists": True}}
            )
            if existing_data is not None:
                _id = existing_data["_id"]
                result = await collection.update_one(
                    {"_id": _id, "_fm_id": _fm_id}, {"$unset": {nested_key: ""}}
                )
                # Validate the upserted data
                if (
                    result.modified_count > 0
                    or result.matched_count > 0
                    or result.upserted_id
                ):
                    valid = True

                # Confirm the modification
                modified_doc = await collection.find_one({"_id": _id, "_fm_id": _fm_id})
                if modified_doc is not None:
                    # Delete the document if only ["_id", "_fm_id"] is there
                    if len(modified_doc.keys()) == 2:
                        await collection.delete_one({"_id": modified_doc["_id"]})

                # Drop collection if no documents exist after deletion
                if await collection.count_documents({}) == 0:
                    await collection.drop()

        # Dropping the collection at db level
        else:
            await collection.drop()
            valid = True

        if not valid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
    return None
