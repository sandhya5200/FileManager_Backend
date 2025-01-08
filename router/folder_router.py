from fastapi import APIRouter, Depends
from fastapi import HTTPException, Depends
from configuration.database import folders_collection, files_collection
from bson import ObjectId
from schema.folder_dto import Folder
from datetime import datetime
from security.jwtConfig import jwtBearer


router = APIRouter(tags=["Folders"]) 

@router.post('/folders')
def create_folder(folder: Folder, current_user: dict = Depends(jwtBearer()) ):
    if not folder.name:
        raise HTTPException(status_code=400,detail="Folder name cannot be empty.")
    
    if len(folder.name) < 3:
        raise HTTPException(status_code=400,detail="Folder name must be at least 3 characters long.")

    if not folder.parent_folder_id:
        raise HTTPException(status_code=400,detail="Parent folder ID cannot be null.")
    
    if not ObjectId.is_valid(folder.parent_folder_id):
        raise HTTPException(status_code=400,detail="Invalid parent folder ID.")

    existing_folder = folders_collection.find_one({ "name": folder.name,"parent_folder_id": ObjectId(folder.parent_folder_id)})
    
    if existing_folder:
        raise HTTPException(status_code=400, detail="Folder name already exists under the same parent. Use another name.")
        
    parent_folder = folders_collection.find_one({"_id": ObjectId(folder.parent_folder_id)})
    if not parent_folder:
        raise HTTPException(status_code=404,detail="Parent folder not found.")

    new_folder = {
        "name": folder.name,
        "parent_folder_id": ObjectId(folder.parent_folder_id),
        "created_at": datetime.now()
    }
    result = folders_collection.insert_one(new_folder)

    return {
        "message": "Folder has been created successfully",
        "folder_id": str(result.inserted_id)
    }


@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: str, current_user: dict = Depends(jwtBearer())):

    if not ObjectId.is_valid(folder_id):
        raise HTTPException(status_code=400,detail="Invalid folder ID. Please check and provide a valid ID.")

    deleted = folders_collection.delete_one({"_id": ObjectId(folder_id)})
    if deleted.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found. It may have already been deleted or does not exist.")

    return {"message": "The folder has been deleted successfully"}

@router.put("/update-folder-name/{folder_id}")
def update_folder_name(folder_id: str, new_folder_name: str, current_user: dict = Depends(jwtBearer())):
    if not ObjectId.is_valid(folder_id):
        raise HTTPException(status_code=400, detail="Invalid folder ID.")
    
    folder_document = folders_collection.find_one({"_id": ObjectId(folder_id)})
    if not folder_document:
        raise HTTPException(status_code=404, detail="Folder not found.")
    
    if folder_document.get("name") == new_folder_name:
        raise HTTPException(
            status_code=400, 
            detail="The new folder name cannot be the same as the current name."
        )
    
    folders_collection.update_one(
        {"_id": ObjectId(folder_id)},
        {"$set": {"name": new_folder_name}}
    )

    return {"message": "Folder name has been updated successfully"}


@router.get("/folders/{folder_name}")
def list_folder_contents(folder_name: str, current_user: dict = Depends(jwtBearer())):
    folder = folders_collection.find_one({"name": folder_name})
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found.")

    folder_id = folder["_id"]

    subfolders = list(folders_collection.find({"parent_folder_id": folder_id}))
    files = list(files_collection.find({"folder_id": folder_id}))

    subfolders_data = [{"id": str(subfolder["_id"]), "name": subfolder["name"]} for subfolder in subfolders]
    files_data = [{"id": str(file["_id"]), "name": file["filename"]} for file in files]

    return {
        "folder_name": folder_name,
        "subfolders": subfolders_data,
        "files": files_data
    }