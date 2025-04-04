from pydantic import BaseModel
from datetime import datetime


class Task(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    status: int
    priority: int
    estimated_end_date: datetime
    date_created: datetime
    date_modified: datetime


class TaskListResponse(BaseModel):
    count: int
    results: list[Task]
