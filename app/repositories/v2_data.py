from typing import Any

from app.db.database import get_collection, get_database
from app.domain.firebase_path import FirebasePath
from app.repositories.indexes import RULES_COLLECTION

ID_FIELD = "_fm_id"
VALUE_FIELD = "_fm_val"
ID_INDEX = "_fm_id_"


class V2DataRepository:
    """MongoDB persistence for the v2 ``_fm_id``/``_fm_val`` representation."""

    async def ensure_collection(self, collection_name: str) -> Any:
        collection = get_collection(collection_name)
        await collection.create_index(ID_FIELD, unique=True, name=ID_INDEX)
        return collection

    async def replace_collection(self, collection_name: str, data: dict | list) -> None:
        collection = get_collection(collection_name)
        await collection.drop()
        collection = await self.ensure_collection(collection_name)
        documents = self.encode_documents(data)
        if documents:
            await collection.insert_many(documents, ordered=False)

    async def insert_record(self, collection_name: str, record_id: str, value: Any) -> None:
        collection = await self.ensure_collection(collection_name)
        await collection.insert_one({ID_FIELD: record_id, VALUE_FIELD: value})

    async def set_value(self, path: FirebasePath, value: Any) -> None:
        if path.record_id is None:
            raise ValueError("A record id is required when setting a value")

        collection = await self.ensure_collection(path.collection)
        await collection.update_one(
            {ID_FIELD: path.record_id},
            {"$set": {path.mongo_value_path: value}},
            upsert=True,
        )

    async def delete(self, path: FirebasePath) -> None:
        collection = get_collection(path.collection)
        if path.is_collection:
            await collection.drop()
            return

        if path.child_segments:
            await collection.update_one(
                {ID_FIELD: path.record_id},
                {"$unset": {path.mongo_value_path: ""}},
            )
        else:
            await collection.delete_one({ID_FIELD: path.record_id})

        if await collection.count_documents({}) == 0:
            await collection.drop()

    async def drop_all(self) -> None:
        database = get_database()
        for collection_name in await database.list_collection_names():
            await get_collection(collection_name).drop()

    async def read_root(self) -> dict:
        collection_names = await get_database().list_collection_names()
        collection_names = sorted(name for name in collection_names if name not in {"__fm_root__", RULES_COLLECTION})
        return {name: await self.read_collection(name) for name in collection_names}

    async def read_collection(self, collection_name: str) -> dict:
        documents = await get_collection(collection_name).find({}, {"_id": 0}).sort(ID_FIELD, 1).to_list(length=None)
        return {document[ID_FIELD]: document[VALUE_FIELD] for document in documents}

    async def read(self, path: FirebasePath) -> Any:
        if path.is_collection:
            return await self.read_collection(path.collection)

        document = await get_collection(path.collection).find_one(
            {ID_FIELD: path.record_id},
            {"_id": 0},
        )
        if document is None:
            return None

        value = document[VALUE_FIELD]
        for segment in path.child_segments:
            try:
                value = value[int(segment)] if isinstance(value, list) else value[segment]
            except (IndexError, KeyError, TypeError, ValueError):
                return None
        return value

    @staticmethod
    def encode_documents(data: dict | list) -> list[dict]:
        items = enumerate(data) if isinstance(data, list) else data.items()
        return [{ID_FIELD: str(key), VALUE_FIELD: value} for key, value in items]
