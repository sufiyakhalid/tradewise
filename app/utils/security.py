from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from app.db import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.users.find_one({"contact_number": payload.get("sub")})
        if user:
            return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
