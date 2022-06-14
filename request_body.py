from pydantic import BaseModel


class RequestBody(BaseModel):
    source: str
    destination: str
    distance: str

