from dataclasses import dataclass
from typing import Any

from app.domain.query import QuerySpec

_MISSING = object()


@dataclass(frozen=True, slots=True)
class QueryEntry:
    key: Any
    value: Any
    ordered_value: Any


class FirebaseQueryEngine:
    """Apply Firebase ordering, filtering, and limits to decoded JSON data."""

    def apply(self, value: Any, query: QuerySpec) -> Any:
        order_by = query.normalized_order_by
        if order_by is None or not isinstance(value, (dict, list)):
            return value

        is_list = isinstance(value, list)
        items = list(enumerate(value)) if is_list else list(value.items())
        entries = self._ordered_entries(items, order_by, is_list=is_list)
        entries = self._filter_entries(entries, query, order_by=order_by, is_list=is_list)

        if query.limit_to_first is not None:
            entries = entries[: query.limit_to_first]
        if query.limit_to_last is not None:
            entries = entries[-query.limit_to_last :] if query.limit_to_last else []

        if is_list:
            return [entry.value for entry in entries]
        return {entry.key: entry.value for entry in entries}

    def _ordered_entries(
        self,
        items: list[tuple[Any, Any]],
        order_by: str,
        *,
        is_list: bool,
    ) -> list[QueryEntry]:
        entries = []
        for key, value in items:
            if order_by == "$key":
                ordered_value = key if is_list else str(key)
            elif order_by == "$value":
                ordered_value = value
            else:
                ordered_value = self._get_child(value, order_by)
                if ordered_value is _MISSING:
                    continue
            entries.append(QueryEntry(key, value, ordered_value))

        if order_by == "$key":
            return sorted(entries, key=lambda entry: entry.ordered_value)
        return sorted(entries, key=lambda entry: (self._value_sort_key(entry.ordered_value), str(entry.key)))

    def _filter_entries(
        self,
        entries: list[QueryEntry],
        query: QuerySpec,
        *,
        order_by: str,
        is_list: bool,
    ) -> list[QueryEntry]:
        start_at = self._coerce_key_bound(query.start_at, is_list) if order_by == "$key" else query.start_at
        end_at = self._coerce_key_bound(query.end_at, is_list) if order_by == "$key" else query.end_at
        equal_to = self._coerce_key_bound(query.equal_to, is_list) if order_by == "$key" else query.equal_to

        if start_at is not None:
            entries = [entry for entry in entries if self._compare(entry.ordered_value, start_at) >= 0]
        if end_at is not None:
            entries = [entry for entry in entries if self._compare(entry.ordered_value, end_at) <= 0]
        if equal_to is not None:
            entries = [entry for entry in entries if self._compare(entry.ordered_value, equal_to) == 0]
        return entries

    @staticmethod
    def _get_child(value: Any, child_path: str) -> Any:
        current = value
        for component in child_path.strip("/").split("/"):
            if not isinstance(current, dict) or component not in current:
                return _MISSING
            current = current[component]
        return current

    @classmethod
    def _compare(cls, left: Any, right: Any) -> int:
        left_key = cls._value_sort_key(left)
        right_key = cls._value_sort_key(right)
        return (left_key > right_key) - (left_key < right_key)

    @staticmethod
    def _coerce_key_bound(value: Any, is_list: bool) -> Any:
        if value is None:
            return None
        if is_list:
            return int(value)
        return str(value)

    @classmethod
    def _value_sort_key(cls, value: Any) -> tuple:
        if value is None:
            return (0,)
        if isinstance(value, bool):
            return (1, value)
        if isinstance(value, (int, float)):
            return (2, value)
        if isinstance(value, str):
            return (3, value)
        if isinstance(value, list):
            return (4, tuple(cls._value_sort_key(item) for item in value))
        if isinstance(value, dict):
            return (5, tuple((key, cls._value_sort_key(item)) for key, item in value.items()))
        return (6, repr(value))
