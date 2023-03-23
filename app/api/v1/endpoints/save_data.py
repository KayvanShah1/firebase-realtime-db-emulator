import uuid
from fastapi import APIRouter, HTTPException, status


from app.db.database import base_collection, get_collection
from app.schemas.data import PostDataResponse

router = APIRouter()


async def _if_structure_exists(collection, key: str) -> bool:
    """_summary_

    Args:
        collection (_type_): _description_
        key (str): _description_

    Returns:
        _type_: _description_
    """
    resp = await collection.find_one({key: {"$exists": True}})
    if resp is not None:
        return True
    return False


def _check_empty_payload(payload) -> Exception:
    """_summary_

    Args:
        payload (_type_): _description_

    Raises:
        HTTPException: _description_
    """
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data cannot be None"
        )


@router.post(
    "/.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def push_data_root(data: str | list | dict | bool = None) -> dict:
    _check_empty_payload(data)

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    data = {id: data}

    collection = base_collection

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
    "/.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully created data document",
)
async def put_data_root(
    data: str | list | dict | bool = None,
) -> str | list | dict | bool:
    _check_empty_payload(data)
    og_data = data
    # collection = base_collection
    collection = get_collection("demo")
    await collection.drop()
    # Push Data
    new_data = await collection.insert_one(data)
    # Validation
    valid = await collection.find_one({"_id": new_data.inserted_id}, {"_id": 0})

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
async def delete_data_root() -> None:
    await base_collection.drop()
    return None


@router.post(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data(path: str, data: str | list | dict | bool = None) -> dict:
    _check_empty_payload(data)

    # collection = get_collection(path_components[0])
    collection = base_collection

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    data = {id: data}

    path_components = path.strip("/").split("/")

    # Recreate MongoDB style key
    nested_key = ".".join(path_components)
    if await _if_structure_exists(collection, nested_key):
        existing_data = await collection.find_one({nested_key: {"$exists": True}})
        _id = existing_data["_id"]

        # Traverse and update existing sub-document
        for key in path_components:
            existing_data = existing_data[key]
        existing_data.update(data)

        # Update existing sub-document
        new_data = await collection.update_one(
            {"_id": _id}, {"$set": {nested_key: existing_data}}, upsert=True
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
async def put_data(
    path: str, data: str | list | dict | bool = None
) -> str | list | dict | bool:
    _check_empty_payload(data)

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

        # Update existing sub-document
        new_data = await collection.update_one(
            {"_id": _id}, {"$set": {nested_key: data}}, upsert=True
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


@router.patch(
    "/{path:path}.json",
    status_code=status.HTTP_201_CREATED,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def update_data(path: str, data: dict):
    return None


@router.delete(
    "/{path:path}.json",
    status_code=status.HTTP_200_OK,
    response_description="Sucessfully deleted",
)
async def delete_data(path: str):
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

            # Confirm the modification
            modified_doc = await collection.find_one({"_id": _id})
            if modified_doc is not None:
                # Delete the document if only "_id" is there
                if len(modified_doc.keys()) == 1:
                    await collection.delete_one({"_id": modified_doc["_id"]})
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Key doesn't exist"
        )
    return None
