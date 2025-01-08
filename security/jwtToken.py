from fastapi import HTTPException
from jose import jwt, JWTError
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

class JwtToken:
        
    def create_access_token(data: dict, expires_delta: timedelta | None = None):   #none is given to fallback to default time when not specified
        to_encode = data.copy()
        expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str): #validates and decodes the token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  #payload means the data inside the token
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")


