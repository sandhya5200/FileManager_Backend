✅ Technologies & Features You’ve Implemented
🔐 User Authentication & Authorization
    • JWT-based login with token generation (jwtBearer, JwtToken)
    • Password hashing using bcrypt
    • Role-based access (ADMIN, USER) defined using an Enum
    • Face authentication on login using face_recognition library
    • Image capture and storage via capture_image function
    • Image storage in MongoDB using GridFS
🧍 User Routes (user_router.py)
    • POST /signup:
        ◦ Validates input
        ◦ Captures user image
        ◦ Hashes password
        ◦ Stores user with role and image in MongoDB
    • POST /login:
        ◦ Validates credentials
        ◦ Captures live image and compares with stored one
        ◦ Generates JWT token if matched
    • PATCH /update-password:
        ◦ Validates old password
        ◦ Updates to new hashed password

🗂️ Folder Management (folder_router.py)
    • POST /folders:
        ◦ Creates a folder with name and parent folder ID
    • DELETE /folders/{id}:
        ◦ Only admins can delete folders
    • PUT /update-folder-name/{id}:
        ◦ Update folder name with validation
    • GET /folders/{id}:
        ◦ Lists folder contents (subfolders & files)

📁 File Management (files_router.py)
    • File types: JPEG, PNG, PDF only
    • Stored using GridFS
    • File metadata saved in files_metadata collection
    • POST /upload:
        ◦ Upload file to folder
        ◦ Checks for duplicate names
    • DELETE /delete-file/{id}:
        ◦ Admin-only deletion
    • PUT /update-file-name/{id}:
        ◦ Update name with validation
    • GET /files/download-by-id/{id}:
        ◦ Downloads file with StreamingResponse

📦 Backend Architecture
    • FastAPI for backend APIs
    • MongoDB with pymongo + GridFS for file/image storage
    • JWT tokens for secured routes and user sessions
    • Folder-File hierarchy: Folders store child folders and files using parent_folder_id & folder_id
    • Face recognition authentication adds a biometric layer

▶️ How to Run This Project Locally
🛠️ 1. Requirements
Make sure you have:
    • Python 3.10+
    • MongoDB running locally or MongoDB Atlas URI
    • Webcam access (for face_recognition)
    • Install dependencies:
pip install fastapi uvicorn pymongo bcrypt python-multipart face_recognition python-jose[cryptography] gridfs
NOTE – No need of creating any database automatically when we run the project the databases and tables are created.
📁 2. Project Structure (Example)

project/
│
├── main.py
├── router/
│   ├── user_router.py
│   ├── files_router.py
│   └── folder_router.py
├── configuration/
│   └── database.py
├── schema/
│   ├── user_dto.py
│   └── folder_dto.py
├── security/
│   ├── jwtToken.py
│   └── jwtConfig.py
├── utility/
│   └── common.py  # (capture_image function)


⚙️ 3. Run FastAPI Server
uvicorn main:app --reload
🌐 4. Test with Swagger UI
Navigate to:
http://127.0.0.1:8000/docs


