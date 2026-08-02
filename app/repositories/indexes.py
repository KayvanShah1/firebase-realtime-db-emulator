from typing import Any

from app.db.database import get_collection

RULES_COLLECTION = "__fm_rules__"
ROOT_RULE_PATH = "__root__"


class IndexRepository:
    """Persist and retrieve Firebase index rules."""

    @property
    def collection(self) -> Any:
        return get_collection(RULES_COLLECTION)

    @staticmethod
    def normalize_path(path: str | None) -> str:
        return path or ROOT_RULE_PATH

    async def get(self, path: str | None = None) -> str | dict | list | None:
        normalized_path = self.normalize_path(path)
        document = await self.collection.find_one({"path": normalized_path}, {"_id": 0})
        return document["indexOn"] if document is not None else None

    async def set(self, path: str | None, index_on: str | dict | list) -> dict:
        normalized_path = self.normalize_path(path)
        await self.collection.create_index("path", unique=True, name="_fm_path_")
        await self.collection.update_one(
            {"path": normalized_path},
            {"$set": {"indexOn": index_on}},
            upsert=True,
        )
        return {"path": normalized_path, "indexOn": index_on}

    async def delete(self, path: str | None = None) -> bool:
        normalized_path = self.normalize_path(path)
        result = await self.collection.delete_one({"path": normalized_path})
        return result.deleted_count > 0

    async def list_rules(self) -> dict:
        rules = {}
        documents = await self.collection.find({}, {"_id": 0}).to_list(length=None)
        for document in documents:
            key = "indexOn" if document["path"] == ROOT_RULE_PATH else document["path"]
            rules[key] = document["indexOn"]
        return rules
