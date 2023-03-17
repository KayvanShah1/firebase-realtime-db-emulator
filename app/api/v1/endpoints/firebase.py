import uuid
from bson import ObjectId
import pymongo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.db.database import get_collection, db
from app.schemas.data import Data, DataModel, PostDataResponse

router = APIRouter()


@router.post(
    "/{path:path}.json",
    status_code=status.HTTP_201_CREATED,
    response_model=PostDataResponse,
    response_description="Sucessfully created data document",
)
async def post_data(path: str, data: dict):
    path_components = path.strip("/").split("/")
    collection = get_collection(path_components[0])

    # Create a new ID for data to insert
    id = uuid.uuid4().hex
    data = {id: data}

    # Traverse over the path components
    for key in path_components:
        data = {key: data}

    # Push Data
    new_data = await collection.insert_one(data)
    created_data = await collection.find_one({"_id": new_data.inserted_id})
    if not created_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return {"name": id}
