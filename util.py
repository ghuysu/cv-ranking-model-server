import jwt
from fastapi import HTTPException, status, Request
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv
import os

load_dotenv()

def verify_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header invalid",
            )
        token = auth_header[len("Bearer "):]
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms='HS256')
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid",
        )