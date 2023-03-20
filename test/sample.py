import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["firebase_db"]

# Generic Collection
base_collection = db["firebase_collection"]
base_collection.insert_one({"x": 23})
