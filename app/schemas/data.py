from typing import Any, Dict, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.db.utils import PyObjectId


class DataModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    data: Any

    class Config:
        json_encoders = {ObjectId: str}


class PostDataResponse(BaseModel):
    name: str
