# app/schemas/user.py
from pydantic import BaseModel
from typing import List

class CurrentUser(BaseModel):
    id: int  # Must match your external_user_id type
    email: str
    is_active: bool = True
    roles: List[str] = []

    class Config:
        from_attributes = True  # Pydantic v2 style