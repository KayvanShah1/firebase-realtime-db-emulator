from typing import Any
from pydantic import BaseModel


class PostDataResponse(BaseModel):
    name: str


class GetDataResponse(BaseModel):
    __root__: Any
