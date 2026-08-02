import uuid
from collections.abc import Callable
from typing import Any

from app.domain.firebase_path import FirebasePath
from app.repositories.v2_data import V2DataRepository


class V2DataService:
    """Implement v2 write semantics independently from HTTP routing."""

    def __init__(
        self,
        repository: V2DataRepository | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository or V2DataRepository()
        self.id_factory = id_factory or (lambda: uuid.uuid4().hex)

    async def push_root(self, data: dict) -> str:
        generated_id = self.id_factory()
        await self.repository.replace_collection(generated_id, data)
        return generated_id

    async def put_root(self, data: dict[str, dict]) -> dict[str, dict]:
        for collection_name, value in data.items():
            await self.repository.replace_collection(collection_name, value)
        return data

    async def delete_root(self) -> None:
        await self.repository.drop_all()

    async def push(self, path: FirebasePath, data: Any) -> str:
        generated_id = self.id_factory()
        if data is None:
            return generated_id

        if path.is_collection:
            await self.repository.insert_record(path.collection, generated_id, data)
        else:
            await self.repository.set_value(path.append(generated_id), data)
        return generated_id

    async def put(self, path: FirebasePath, data: Any) -> Any:
        if data is None or not isinstance(data, (dict, int, float, str, list, bool)):
            raise TypeError("Unsupported JSON value")
        if path.is_collection:
            if not isinstance(data, (dict, list)):
                raise TypeError("Only dictionaries and lists can replace a collection")
            await self.repository.replace_collection(path.collection, data)
        else:
            await self.repository.set_value(path, data)
        return data

    async def patch(self, path: FirebasePath, data: dict) -> dict:
        for relative_path, value in data.items():
            await self.repository.set_value(path.append(relative_path), value)
        return data

    async def delete(self, path: FirebasePath) -> None:
        await self.repository.delete(path)
