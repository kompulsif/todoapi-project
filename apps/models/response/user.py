from pydantic import BaseModel
from datetime import datetime


class User(BaseModel):
    id: int
    visibility_name: str
    email: str
    user_approved: bool
    two_factor_auth: bool
    password: str
    date_created: datetime
    date_modified: datetime
