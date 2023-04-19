import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["firebase_db"]

# Generic Collection
base_collection = db["sample-dummy"]
doc = base_collection.find({}, {"_id": 0}).sort([("_fm_val", 1)])

print(list(doc))
