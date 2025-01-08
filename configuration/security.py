# from fastapi.security import OAuth2PasswordBearer
# from jose import jwt, JWTError
# from datetime import datetime, timedelta
# from fastapi import HTTPException, Depends
# from configuration.database import users_collection
# import os
# from dotenv import load_dotenv

# load_dotenv()
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  
# #generates jwt token with the users data and expiration time
# def create_access_token(data: dict, expires_delta: timedelta | None = None):   #none is given to fallback to default time when not specified
#     to_encode = data.copy()
#     expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def verify_token(token: str): #validates and decodes the token
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  #payload means the data inside the token
#         return payload
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

# def get_current_user(token: str = Depends(oauth2_scheme)): #extracts the user from token by verifying and querying the database for the user details
#     payload = verify_token(token)
#     username = payload.get("username")
#     if not username:
#         raise HTTPException(status_code=401, detail="Invalid token payload")
#     user = users_collection.find_one({"username": username})
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")
#     return user