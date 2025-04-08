from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
from datetime import datetime
from io import BytesIO
from pymongo import MongoClient
from gridfs import GridFS
from configuration.database import mongo_uri, database
from security.jwtConfig import jwtBearer
from schema.user_dto import Role

router = APIRouter(tags=["Files"])

client = MongoClient(mongo_uri)  # Update with your connection settings

fs = GridFS(database)  # Initialize GridFS

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    input_folder_id: str = Form(...),
    current_user: dict = Depends(jwtBearer()),
):
    allowed_file_types = ["image/jpeg", "image/png", "application/pdf"]  # Allowed types
    if file.content_type not in allowed_file_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, and PDF files are allowed."
        )

    if not input_folder_id or not ObjectId.is_valid(input_folder_id):
        raise HTTPException(status_code=400, detail="Invalid or missing parent folder ID.")

    # Use the original file name
    file_name = file.filename
    if not file_name or len(file_name.strip()) < 3:
        raise HTTPException(status_code=400, detail="File name must have at least 3 characters.")

    # Check for duplicate file names in the same folder
    existing_file = database.files_metadata.find_one({"filename": file_name, "folder_id": ObjectId(input_folder_id)})
    if existing_file:
        raise HTTPException(status_code=409, detail="A file with the same name already exists in the specified folder.")

    # Save file in GridFS
    file_content = await file.read()

    try:
        file_id = fs.put(file_content, filename=file_name, folder_id=ObjectId(input_folder_id), content_type=file.content_type)
        metadata = {
            "filename": file_name,
            "folder_id": ObjectId(input_folder_id),
            "gridfs_id": file_id,  # Reference to GridFS file
            "content_type": file.content_type,
            "created_at": datetime.now(),
        }
        database.files_metadata.insert_one(metadata)  # Store file metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while saving the file: {str(e)}")

    return {"message": "File uploaded successfully", "file_id": str(file_id)}



@router.delete("/delete-file/{file_id}")
async def delete_file(file_id: str, current_user: dict = Depends(jwtBearer())):

    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403,detail="Only admins have access to delete the files")
    
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID.")

    file_metadata = database.files_metadata.find_one({"gridfs_id": ObjectId(file_id)})
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        fs.delete(ObjectId(file_id))  # Delete file from GridFS
        database.files_metadata.delete_one({"gridfs_id": ObjectId(file_id)})  # Delete metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the file: {str(e)}")

    return {"message": "File has been deleted successfully"}


@router.put("/update-file-name/{file_id}")
async def update_file_name(file_id: str, new_file_name: str, current_user: dict = Depends(jwtBearer())):
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID.")

    file_metadata = database.files_metadata.find_one({"_id": ObjectId(file_id)})
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found.")

    if file_metadata.get("filename") == new_file_name:
        raise HTTPException(status_code=400, detail="The new file name cannot be the same as the current name.")

    try:
        database.files_metadata.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": {"filename": new_file_name}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the file name: {str(e)}")

    return {"message": "File name has been updated successfully"}


@router.get("/files/download-by-id/{file_id}")
async def download_file_by_id(file_id: str, current_user: dict = Depends(jwtBearer())):
    try:
        # Convert the file_id to an ObjectId
        file_object_id = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file ID format.")

    # Retrieve the file metadata
    file_metadata = database.files_metadata.find_one({"_id": file_object_id})
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found.")


    try:
        gridfs_file = fs.get(file_metadata["gridfs_id"])  # Retrieve file from GridFS
    except Exception:
        raise HTTPException(status_code=500, detail="File content is missing or corrupted.")

    return StreamingResponse(
        BytesIO(gridfs_file.read()),
        media_type=file_metadata.get("content_type", "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{file_metadata["filename"]}"'}
    )

# Why Use async in this code particularly
# File Operations:

# Uploading and downloading files involve reading and writing large chunks of data, which are inherently I/O operations.
# async ensures that while the program waits for these operations (e.g., file reading or writing), 
# it doesn’t block the server from handling other requests.