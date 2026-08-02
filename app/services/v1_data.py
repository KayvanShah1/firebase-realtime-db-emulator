import uuid
from collections.abc import Callable
from typing import Any

from app.domain.firebase_path import FirebasePath
from app.repositories.v1_legacy import LegacyV1Repository


class EmptyV1PayloadError(ValueError):
    pass


class V1DataService:
    """Preserve the deprecated v1 API over its legacy storage adapter."""

    def __init__(
        self,
        repository: LegacyV1Repository | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository or LegacyV1Repository()
        self.id_factory = id_factory or (lambda: uuid.uuid4().hex)

    async def get(self, path: FirebasePath | None = None) -> Any:
        return await self.repository.read(path)

    async def push_root(self, data: Any) -> str:
        self.require_payload(data)
        generated_id = self.id_factory()
        await self.repository.insert_document({generated_id: data})
        return generated_id

    async def put_root(self, data: dict) -> dict:
        self.require_payload(data)
        await self.repository.replace_root(data)
        return data

    async def delete_root(self) -> None:
        await self.repository.delete_root()

    async def push(self, path: FirebasePath, data: Any) -> str:
        self.require_payload(data)
        generated_id = self.id_factory()
        await self.repository.set_value(path.append(generated_id), data)
        return generated_id

    async def put(self, path: FirebasePath, data: Any) -> Any:
        self.require_payload(data)
        await self.repository.set_value(path, data)
        return data

    async def patch(self, path: FirebasePath, data: Any) -> Any:
        if isinstance(data, dict):
            for relative_path, value in data.items():
                await self.repository.set_value(path.append(relative_path), value)
        else:
            await self.repository.set_value(path, data)
        return data

    async def delete(self, path: FirebasePath) -> bool:
        return await self.repository.delete(path)

    @staticmethod
    def require_payload(data: Any) -> None:
        if data is None:
            raise EmptyV1PayloadError("Data cannot be None")
