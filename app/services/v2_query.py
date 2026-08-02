from typing import Any

from app.domain.firebase_path import FirebasePath
from app.domain.query import QuerySpec
from app.domain.query_engine import FirebaseQueryEngine
from app.repositories.indexes import IndexRepository
from app.repositories.v2_data import V2DataRepository


class QueryRuleError(ValueError):
    """Raised when a query requires a rule that has not been configured."""


class V2QueryService:
    def __init__(
        self,
        data_repository: V2DataRepository | None = None,
        index_repository: IndexRepository | None = None,
        engine: FirebaseQueryEngine | None = None,
    ) -> None:
        self.data_repository = data_repository or V2DataRepository()
        self.index_repository = index_repository or IndexRepository()
        self.engine = engine or FirebaseQueryEngine()

    async def get_root(self, query: QuerySpec) -> dict:
        value = await self.data_repository.read_root()
        await self._require_index(query, path=None)
        return self.engine.apply(value, query)

    async def get(self, path: FirebasePath, query: QuerySpec) -> Any:
        value = await self.data_repository.read(path)
        await self._require_index(query, path=path)
        return self.engine.apply(value, query)

    async def _require_index(self, query: QuerySpec, path: FirebasePath | None) -> None:
        order_by = query.normalized_order_by
        if order_by in {None, "$key"}:
            return

        required_index = ".value" if order_by == "$value" else order_by
        rule_path = path.raw if path is not None else None
        configured_index = await self.index_repository.get(rule_path)
        if self._contains_index(configured_index, required_index):
            return

        display_path = f"/{path.raw}" if path is not None else "/"
        raise QueryRuleError(
            f'Index not defined, add ".indexOn": "{required_index}", for path "{display_path}", to the rules'
        )

    @staticmethod
    def _contains_index(configured_index: str | dict | list | None, required_index: str) -> bool:
        if isinstance(configured_index, str):
            return configured_index == required_index
        if isinstance(configured_index, (dict, list)):
            return required_index in configured_index
        return False
