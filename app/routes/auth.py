from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.errors import AppError, RateLimiter, ok
from app.models.user import RevokedToken, User
from app.schemas.auth import LoginIn, RegisterIn
from app.security.auth import create_token, get_token_payload
from app.security.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
_limit = RateLimiter(10, 60)


@router.post("/register", status_code=201, dependencies=[Depends(_limit)])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(func.lower(User.username) == body.username.lower())):
        raise AppError(409, "Username นี้ถูกใช้แล้ว")
    if db.scalar(select(User).where(func.lower(User.email) == body.email.lower())):
        raise AppError(409, "Email นี้ถูกใช้แล้ว")
    user = User(username=body.username, email=body.email.lower(),
                password_hash=hash_password(body.password),
                display_name=body.display_name or body.username)
    db.add(user)
    db.commit()
    return ok({"id": user.id, "username": user.username, "email": user.email})


@router.post("/login", dependencies=[Depends(_limit)])
def login(body: LoginIn, db: Session = Depends(get_db)):
    ident = body.identifier.lower()
    user = db.scalar(select(User).where(or_(func.lower(User.username) == ident, User.email == ident)))
    if not user or not verify_password(body.password, user.password_hash):
        raise AppError(401, "Username/Email หรือรหัสผ่านไม่ถูกต้อง")
    return ok({"access_token": create_token(user.id), "token_type": "bearer"})


@router.post("/logout")
def logout(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    if not db.get(RevokedToken, payload["jti"]):
        db.add(RevokedToken(jti=payload["jti"], expires_at=datetime.utcfromtimestamp(payload["exp"])))
        db.commit()
    return ok({"message": "ออกจากระบบแล้ว"})
