from fastapi import APIRouter, HTTPException, Depends
from schema.user_dto import User
from configuration.database import users_collection
import bcrypt
from fastapi import Form
from security.jwtToken import JwtToken
from security.jwtConfig import jwtBearer
from fastapi.responses import JSONResponse, StreamingResponse
from gridfs import GridFS
import cv2
import io
from bson import ObjectId
from configuration.database import database
import face_recognition  # Ensure to install this library

fs = GridFS(database)

user_router = APIRouter()

def capture_image():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise HTTPException(status_code=500, detail="Failed to open the camera")

    while True:
        ret, frame = cam.read()
        if not ret:
            raise HTTPException(status_code=500, detail="Failed to capture image")
        cv2.imshow("Camera - Press 'c' to capture, 'q' to quit", frame)
        key = cv2.waitKey(1)

        if key == ord('c'):
            _, buffer = cv2.imencode('.jpg', frame)
            cam.release()
            cv2.destroyAllWindows()
            return io.BytesIO(buffer).getvalue()
        elif key == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            raise HTTPException(status_code=400, detail="Image capture aborted by user")

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

    image_bytes = capture_image()
    image_id = fs.put(image_bytes, content_type="image/jpeg")
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    users_collection.insert_one({"username": user.username, "password": hashed_password, "image_id": str(image_id)})

    return {"message": "You have signed up successfully with face authentication"}

@user_router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    signedup_user = users_collection.find_one({"username": username})
    if not signedup_user:
        raise HTTPException(status_code=400, detail="You have not signed up, please sign up")
    if not bcrypt.checkpw(password.encode("utf-8"), signedup_user["password"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    # Capture current image for authentication
    image_bytes = capture_image()
    stored_image = fs.get(ObjectId(signedup_user["image_id"])).read()

    # Compare captured image with stored image
    try:
        captured_image = face_recognition.load_image_file(io.BytesIO(image_bytes))
        stored_image = face_recognition.load_image_file(io.BytesIO(stored_image))

        captured_encodings = face_recognition.face_encodings(captured_image)
        stored_encodings = face_recognition.face_encodings(stored_image)

        if not captured_encodings or not stored_encodings:
            raise HTTPException(status_code=400, detail="No face detected for comparison")

        match = face_recognition.compare_faces([stored_encodings[0]], captured_encodings[0])

        if not match[0]:
            raise HTTPException(status_code=401, detail="Face authentication failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during face comparison: {str(e)}")

    access_token = JwtToken.create_access_token({"username": username})
    return {"access_token": access_token, "token_type": "bearer"}



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


@user_router.post("/capture-image/")
def capture_and_store_image(current_user: dict = Depends(jwtBearer())):
    try:
        cam = cv2.VideoCapture(0)  #tells the camera number 0 is for default
        if not cam.isOpened():
            raise HTTPException(status_code=500, detail="Failed to open the camera")
        
        while True: 
            ret, frame = cam.read()  #captures frames from the camera on infinite loop
            if ret == False:        
                raise HTTPException(status_code=500, detail="Failed to capture image")
 
            cv2.imshow("Camera - Press 'c' to capture", frame)  #print on camera frame

            key = cv2.waitKey(1)  #waits for ms for a key press

            if key == ord('c'):  #if c is pressed ord returs the ascii value
               
                _, buffer = cv2.imencode('.jpg', frame)   
                image_bytes = io.BytesIO(buffer).getvalue()   #converts the frame to jpeg format 

                image_id = fs.put(image_bytes, content_type="image/jpeg")  # store the image in MongoDB GridFS

                cam.release()
                cv2.destroyAllWindows()

                return JSONResponse(content={"message": "Image captured and stored successfully", "image_id": str(image_id)})

            elif key == ord('q'):  # quit on pressing 'q'
                cam.release()
                cv2.destroyAllWindows()
                raise HTTPException(status_code=400, detail="Image capture aborted by user")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@user_router.get("/get-image/{image_id}")
def get_image(image_id: str, current_user: dict = Depends(jwtBearer())):
    try:
        
        image_id = ObjectId(image_id)
        image = fs.get(image_id)
        image_bytes = image.read()

        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")

    except Exception as e:
        return {"error": f"Image not found: {str(e)}"}





