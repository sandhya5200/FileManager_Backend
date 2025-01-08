from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from security.jwtToken import JwtToken


jwtToken = JwtToken()

class jwtBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super(jwtBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(jwtBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid Token")
            return jwtToken.verify_token(credentials.credentials)
        else:
            raise HTTPException(status_code=403, detail="Invalid Token")