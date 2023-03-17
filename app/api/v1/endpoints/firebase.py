import uuid
from bson import ObjectId
import pymongo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.db.database import get_collection, base_collection
from app.schemas.data import Data, DataModel, PostDataResponse

router = APIRouter()


async def _if_structure_exists(collection, key: str):
    resp = await collection.find_one({key: {"$exists": True}})
    if resp is not None:
        return True
    return False


@router.post(
    "/{path:path}.json",
    status_code=status.HTTP_201_CREATED,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data(path: str, data: dict):
    path_components = path.strip("/").split("/")
    # collection = get_collection(path_components[0])
    collection = base_collection

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    data = {id: data}

    # Traverse over the path components
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
        if new_data.modified_count > 0:
            valid = True
    else:
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
