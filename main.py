from fastapi import FastAPI
from configuration.database import folders_collection
from router.user_router import user_router
from router.folder_router import router as folder_router
from router.files_router import router as files_router
from datetime import datetime
from contextlib import asynccontextmanager

@asynccontextmanager   #using this decorater u can define any logic that should be executed before the application starts
async def lifespan(app: FastAPI):
    root_folder = folders_collection.find_one({"parent_folder_id": None})  #checks if any folder is is there or not
    if not root_folder:
        new_root_folder = {
            "name": "Desktop",
            "parent_folder_id": None,
            "created_at": datetime.now()
        }
        folders_collection.insert_one(new_root_folder)   #creates new folder
        print("Default root folder created successfully.")
    yield   #to continue anything after the application stops instead of return we use 
    print("Application is shutting down.")

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(folder_router)
app.include_router(files_router)
