from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os


load_dotenv(verbose=True)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict,expires_in_hours:int = 24) -> str:
    payload = data.copy()
    payload["iat"]=datetime.utcnow()
    payload["exp"] = datetime.utcnow() + timedelta(expires_in_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
