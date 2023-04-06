from pydantic import BaseModel


class PostDataResponse(BaseModel):
    name: str
