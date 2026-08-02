from copy import deepcopy
from typing import Any

from app.db.database import get_base_collection
from app.domain.firebase_path import FirebasePath


class LegacyV1Repository:
    """Persistence adapter for v1's original nested-document representation."""

    @property
    def collection(self) -> Any:
        return get_base_collection()

    async def insert_document(self, data: dict) -> None:
        await self.collection.insert_one(deepcopy(data))

    async def replace_root(self, data: dict) -> None:
        await self.collection.drop()
        await self.insert_document(data)

    async def delete_root(self) -> None:
        await self.collection.drop()

    async def read(self, path: FirebasePath | None = None) -> Any:
        if path is None:
            return await self.collection.find_one({}, {"_id": 0})

        mongo_path = self.mongo_path(path)
        document = await self.collection.find_one({mongo_path: {"$exists": True}}, {"_id": 0})
        if document is None:
            return None

        value = document
        for segment in path.segments:
            try:
                value = value[int(segment)] if isinstance(value, list) else value[segment]
            except (IndexError, KeyError, TypeError, ValueError):
                return None
        return value

    async def set_value(self, path: FirebasePath, value: Any) -> None:
        mongo_path = self.mongo_path(path)
        document = await self.collection.find_one({path.collection: {"$exists": True}})
        if document is None:
            await self.insert_document(self.wrap(path.segments, value))
            return

        await self.collection.update_one(
            {"_id": document["_id"]},
            {"$set": {mongo_path: deepcopy(value)}},
        )

    async def delete(self, path: FirebasePath) -> bool:
        mongo_path = self.mongo_path(path)
        document = await self.collection.find_one({mongo_path: {"$exists": True}})
        if document is None:
            return False

        await self.collection.update_one(
            {"_id": document["_id"]},
            {"$unset": {mongo_path: ""}},
        )
        modified_document = await self.collection.find_one({"_id": document["_id"]})
        if modified_document is not None and set(modified_document) == {"_id"}:
            await self.collection.delete_one({"_id": document["_id"]})
        return True

    @staticmethod
    def mongo_path(path: FirebasePath) -> str:
        return ".".join(path.segments)

    @staticmethod
    def wrap(segments: tuple[str, ...], value: Any) -> dict:
        wrapped = deepcopy(value)
        for segment in reversed(segments):
            wrapped = {segment: wrapped}
        return wrapped
