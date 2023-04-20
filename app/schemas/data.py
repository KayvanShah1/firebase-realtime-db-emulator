from typing import Any, Optional
from pydantic import BaseModel, BaseConfig

from pydantic.fields import ModelField
from pydantic.typing import is_union, get_args, get_origin


class PostDataResponse(BaseModel):
    name: str


class GetDataResponse(BaseModel):
    __root__: Optional[Any | None] = None
