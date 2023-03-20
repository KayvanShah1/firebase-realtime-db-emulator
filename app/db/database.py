from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.core.settings import MONGODB_URI

try:
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
    except Exception as e:
        print(
            """Unable to connect to Async Mongo Motor... Connecting to standard Motor"""
        )
        client = MongoClient(MONGODB_URI)
except Exception:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to establish connection with client.",
    )

db = client["firebase_db"]

# Generic Collection
base_collection = db["firebase_collection"]


def get_collection(collection_name: str):
    return db[collection_name]
