from typing import Optional

from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    userId: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[str] = None

