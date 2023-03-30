import uuid
from fastapi import APIRouter, HTTPException, status

from app.api.v2.endpoints.utils import (
    _check_empty_payload,
    _check_data_type_for_root,
    _if_structure_exists,
)

from app.db.database import base_collection, get_collection
from app.schemas.data import PostDataResponse

router = APIRouter()


@router.post(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data_root_v2(data: dict = None) -> dict:
    _check_empty_payload(data)

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    collection = get_collection(id)

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
    data: dict = None,
) -> dict:
    _check_empty_payload(data)
    og_data = data
    valid = True
    if type(data) == dict:
        for key, val in data.items():
            # Find and drop old collection with same names
            collection = get_collection(key)
            await collection.drop()

            # Validate and prepare the documents
            _check_data_type_for_root(val)
            docs = [{"_fm_id": k, "_fm_val": v} for k, v in val.items()]
            # Insert the documents
            result = await collection.insert_many(docs, ordered=False)

            # Validate the insertion
            if len(result.inserted_ids) != len(docs):
                valid = False

    if type(data) == list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pushing list on root level is not allowed",
        )

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
    await base_collection.drop()
    return None


@router.post(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data_v2(path: str, data: str | list | dict | bool = None) -> dict:
    _check_empty_payload(data)

    # collection = get_collection(path_components[0])
    collection = base_collection

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    data = {id: data}

    path_components = path.strip("/").split("/")

    # Recreate MongoDB style key
    nested_key = ".".join(path_components)
    parent_key = ".".join(path_components[:-1])
    if len(parent_key) == 0:
        parent_key = nested_key
    if await _if_structure_exists(collection, parent_key):
        existing_data = await collection.find_one({parent_key: {"$exists": True}})
        _id = existing_data["_id"]

        # Traverse and update existing sub-document
        for key in path_components[:-1]:
            existing_data = existing_data[key]
        if not path_components[-1] in existing_data.keys():
            data = {path_components[-1]: data}
            _update_key = parent_key
        else:
            existing_data = existing_data[path_components[-1]]
            _update_key = nested_key
        existing_data.update(data)

        # Update existing sub-document
        new_data = await collection.update_one(
            {"_id": _id}, {"$set": {_update_key: existing_data}}, upsert=True
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
        for key in path_components[::-1]:
            data = {key: data}
        # Push Data
        new_data = await collection.insert_one(data)
        # Validation
        valid = await collection.find_one({"_id": new_data.inserted_id})

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return {"name": id}


@router.put(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully created data document",
)
async def put_data_v2(
    path: str, data: int | float | str | list | dict | bool = None
) -> int | float | str | list | dict | bool:
    _check_empty_payload(data)
    og_data = data

    # Recreate MongoDB style key
    path_components = path.strip("/").split("/")

    # Collection name
    collection = get_collection(path_components[0])

    if len(path_components) >= 1:
        nested_key = ".".join(path_components[1:])
        parent_key = ".".join(path_components[1:-1])

        if len(parent_key) == 0:
            parent_key = nested_key

    return og_data


@router.patch(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully updated data",
)
async def update_data_v2(
    path: str, data: str | list | dict | bool = None
) -> str | list | dict | bool:
    collection = base_collection
    og_data = data

    # Recreate MongoDB style key
    path_components = path.strip("/").split("/")
    nested_key = ".".join(path_components)
    parent_key = ".".join(path_components[:-1])
    if len(parent_key) == 0:
        parent_key = nested_key

    if await _if_structure_exists(collection, parent_key):
        existing_data = await collection.find_one({parent_key: {"$exists": True}})
        _id = existing_data["_id"]

        # Check if data key has path component
        if type(data) is dict:
            _is_path_componment_data = [
                True if "/" in k else False for k in data.keys()
            ]
            if True in _is_path_componment_data:
                setter = {
                    f"{nested_key}.{k.replace('/', '.')}": v for k, v in data.items()
                }
            else:
                setter = {nested_key: data}
        else:
            setter = {nested_key: data}
        # Update existing sub-document
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
        for key in path_components[::-1]:
            data = {key: data}
        # Push Data
        new_data = await collection.insert_one(data)
        # Validation
        valid = await collection.find_one({"_id": new_data.inserted_id})

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
async def delete_data_v2(path: str):
    # collection = get_collection(path_components[0])
    collection = base_collection

    path_components = path.strip("/").split("/")

    # Recreate MongoDB style key
    nested_key = ".".join(path_components)
    if await _if_structure_exists(collection, nested_key):
        # Find the existing document id
        existing_data = await collection.find_one({nested_key: {"$exists": True}})

        # If retrieved document is not NULL
        if existing_data is not None:
            # Drop the field from document
            _id = existing_data["_id"]
            result = await collection.update_one(
                {"_id": _id}, {"$unset": {nested_key: ""}}
            )
            # Validate the upserted data
            if (
                result.modified_count > 0
                or result.matched_count > 0
                or result.upserted_id
            ):
                valid = True

            # Confirm the modification
            modified_doc = await collection.find_one({"_id": _id})
            if modified_doc is not None:
                # Delete the document if only "_id" is there
                if len(modified_doc.keys()) == 1:
                    await collection.delete_one({"_id": modified_doc["_id"]})

        if not valid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Key doesn't exist"
        )
    return None
