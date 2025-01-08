from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

class Folder(BaseModel):
    name: str
    parent_folder_id: str 
