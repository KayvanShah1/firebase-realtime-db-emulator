from motor.motor_asyncio import AsyncIOMotorClient
from app.core.settings import MONGODB_URI


client = AsyncIOMotorClient(MONGODB_URI)
db = client["firebase_db"]

# Generic Collection
base_collection = db["firebase_collection"]


def get_collection(collection_name: str):
    return db[collection_name]
