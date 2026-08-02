import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def decode_query_value(value: Any) -> Any:
    """Decode a Firebase query parameter encoded as a JSON scalar."""
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


class QuerySpec(BaseModel):
    """Validated Firebase query options with Python-friendly field names."""

    model_config = ConfigDict(populate_by_name=True)

    order_by: str | None = Field(default=None, alias="orderBy")
    limit_to_first: int | None = Field(default=None, alias="limitToFirst", ge=0)
    limit_to_last: int | None = Field(default=None, alias="limitToLast", ge=0)
    equal_to: Any = Field(default=None, alias="equalTo")
    start_at: Any = Field(default=None, alias="startAt")
    end_at: Any = Field(default=None, alias="endAt")

    @field_validator("equal_to", "start_at", "end_at", mode="before")
    @classmethod
    def decode_json_scalars(cls, value: Any) -> Any:
        return decode_query_value(value)

    @property
    def normalized_order_by(self) -> str | None:
        return decode_query_value(self.order_by)

    def validation_error(self) -> str | None:
        has_dependent_option = any(
            option is not None
            for option in (
                self.limit_to_first,
                self.limit_to_last,
                self.equal_to,
                self.start_at,
                self.end_at,
            )
        )
        if has_dependent_option and self.order_by is None:
            return "orderBy must be defined when other query parameters are defined"
        if self.limit_to_first is not None and self.limit_to_last is not None:
            return "limitToFirst and limitToLast cannot both be defined"
        return None
