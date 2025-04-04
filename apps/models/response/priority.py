from pydantic import BaseModel


class Priority(BaseModel):
    id: int
    user_id: int
    title: str


class PriorityListResponse(BaseModel):
    count: int
    results: list[Priority]
