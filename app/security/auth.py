import uuid
from datetime import timedelta
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db, utcnow
from app.errors import AppError
from app.models.user import RevokedToken, User

_bearer = HTTPBearer(auto_error=False)
ALGO = "HS256"


def create_token(user_id: int) -> str:
    exp = utcnow() + timedelta(minutes=settings.TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "jti": uuid.uuid4().hex, "exp": exp},
                      settings.SECRET_KEY, algorithm=ALGO)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])
    except jwt.PyJWTError:
        raise AppError(401, "โทเค็นไม่ถูกต้องหรือหมดอายุ")


def get_token_payload(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if cred is None:
        raise AppError(401, "ต้องเข้าสู่ระบบก่อน")
    return decode_token(cred.credentials)


def get_current_user(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)) -> User:
    if db.get(RevokedToken, payload.get("jti")):
        raise AppError(401, "โทเค็นถูกยกเลิกแล้ว")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise AppError(401, "ไม่พบผู้ใช้")
    return user
