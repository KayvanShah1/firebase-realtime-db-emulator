from typing import Any

from pydantic import BaseModel, RootModel


class PostDataResponse(BaseModel):
    name: str


class GetDataResponse(RootModel[Any | None]):
    root: Any | None = None
