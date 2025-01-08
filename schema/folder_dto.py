from pydantic import BaseModel

class Folder(BaseModel):
    name: str
    parent_folder_id: str 
