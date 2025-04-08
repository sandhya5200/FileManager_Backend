from pydantic import BaseModel
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    username: str
    password: str
    role: Role 
