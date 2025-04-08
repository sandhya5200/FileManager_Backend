from fastapi import APIRouter, HTTPException, Depends
from schema.user_dto import User, Role
from configuration.database import users_collection
import bcrypt
from fastapi import Form
from security.jwtToken import JwtToken
from security.jwtConfig import jwtBearer
from gridfs import GridFS
import io
from datetime import timedelta
from bson import ObjectId
from configuration.database import database
import face_recognition  
from utility.common import capture_image

fs = GridFS(database)

user_router = APIRouter(tags=["Users"])

@user_router.post("/signup")
def signup(user: User):
    if not user.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty or just spaces")
    if len(user.username) < 8:
        raise HTTPException(status_code=400, detail="Username should have at least 8 characters")
    if not user.password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty or just spaces")
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password should have at least 8 characters")

    signedup_user = users_collection.find_one({"username": user.username})
    if signedup_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if user.role == Role.ADMIN:
        no_of_admins = users_collection.count_documents({"role": Role.ADMIN.value})
        if no_of_admins >= 1:
            raise HTTPException(status_code=400,detail="Only One admin is allowed") 
        
    image_bytes = capture_image()    #captures the image and coverts it into bytes by calling the function
    image_id = fs.put(image_bytes, content_type="image/jpeg") #the image_id is generated,the captured image bytes stored with content type "image/jpeg".
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())

    users_collection.insert_one({"username": user.username, 
                                "password": hashed_password,
                                "image_id": str(image_id),
                                "role": user.role.value
                                })

    return {"message": f"You have signed up successfully as a {user.role} with face authentication"}


@user_router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    signedup_user = users_collection.find_one({"username": username})
    if not signedup_user:
        raise HTTPException(status_code=400, detail="You have not signed up, please sign up")
    if not bcrypt.checkpw(password.encode("utf-8"), signedup_user["password"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    image_bytes = capture_image()
    stored_image = fs.get(ObjectId(signedup_user["image_id"])).read()

    try:
        captured_image = face_recognition.load_image_file(io.BytesIO(image_bytes))
        stored_image = face_recognition.load_image_file(io.BytesIO(stored_image))

        captured_encodings = face_recognition.face_encodings(captured_image)
        stored_encodings = face_recognition.face_encodings(stored_image)

        if not captured_encodings or not stored_encodings:
            raise HTTPException(status_code=400, detail="No face detected for comparison")

        match = face_recognition.compare_faces([stored_encodings[0]], captured_encodings[0])
        distance = face_recognition.face_distance([stored_encodings[0]], captured_encodings[0])

        if not match[0] or distance[0] > 0.4:
            raise HTTPException(status_code=401, detail="Face authentication failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during face comparison: {str(e)}")
    
    user_role = signedup_user.get("role", "user")  #extracting even the role to include in token

    access_token = JwtToken.create_access_token(
        {"username": username,
         "role": user_role},   #dictionary what ever u want to store in the token
        expires_delta=timedelta(minutes=15)  
    )
    return {"access_token": access_token, 
            "token_type": "bearer",
            "role": user_role}


@user_router.patch("/update-password")
def update_password(old_password: str, new_password: str, current_user: dict = Depends(jwtBearer())):
    db_user = users_collection.find_one({"username": current_user["username"]})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt.checkpw(old_password.encode("utf-8"), db_user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if bcrypt.checkpw(new_password.encode("utf-8"), db_user["password"]):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the current password. Please choose a different password."
        )

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    users_collection.update_one(
        {"username": current_user["username"]}, 
        {"$set": {"password": hashed_password}}
    )
    
    return {"message": "Password has been updated successfully"}



