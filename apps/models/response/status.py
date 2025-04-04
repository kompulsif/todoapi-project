from pydantic import BaseModel


class Status(BaseModel):
    id: int
    user_id: int
    title: str
    default_status: bool


class StatusListResponse(BaseModel):
    count: int
    results: list[Status]
