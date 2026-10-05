import os
import uuid
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.errors import AppError, ok
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.user import ProfileUpdate
from app.security.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
MAX_AVATAR = 2 * 1024 * 1024
# content-type -> (extension, magic-bytes check)
AVATAR_TYPES = {"image/png": ("png", b"\x89PNG"), "image/jpeg": ("jpg", b"\xff\xd8\xff"), "image/webp": ("webp", b"RIFF")}


def _avatar_url(u: User) -> str | None:
    return f"/media/avatars/{u.avatar_path}" if u.avatar_path else None


def _private(db: Session, u: User) -> dict:
    convs = db.scalar(select(func.count(Conversation.id)).where(Conversation.user_id == u.id)) or 0
    msgs = db.scalar(select(func.count(Message.id)).join(Conversation).where(Conversation.user_id == u.id)) or 0
    ai = db.scalar(select(func.count(Message.id)).join(Conversation)
                   .where(Conversation.user_id == u.id, Message.role == "assistant")) or 0
    return {"id": u.id, "username": u.username, "display_name": u.display_name, "bio": u.bio,
            "email": u.email, "avatar_url": _avatar_url(u), "created_at": u.created_at.isoformat(),
            "is_verified": u.is_verified,
            "stats": {"conversations": convs, "messages": msgs, "ai_replies": ai}}


def _delete_avatar_file(u: User) -> None:
    if u.avatar_path:
        try:
            os.remove(os.path.join(settings.UPLOAD_DIR, "avatars", u.avatar_path))
        except OSError:
            pass


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(_private(db, user))


@router.patch("/me")
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.username is not None and body.username.lower() != user.username.lower():
        if db.scalar(select(User).where(func.lower(User.username) == body.username.lower())):
            raise AppError(409, "Username นี้ถูกใช้แล้ว")
    if body.username is not None:
        user.username = body.username
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.bio is not None:
        user.bio = body.bio
    db.commit()
    return ok(_private(db, user))


@router.post("/me/avatar")
async def upload_avatar(file: UploadFile, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    spec = AVATAR_TYPES.get(file.content_type or "")
    if not spec:
        raise AppError(400, "รองรับเฉพาะไฟล์ PNG, JPEG, WEBP")
    data = await file.read(MAX_AVATAR + 1)
    if len(data) > MAX_AVATAR:
        raise AppError(413, "ไฟล์ Avatar ต้องไม่เกิน 2MB")
    if not data.startswith(spec[1]):
        raise AppError(400, "เนื้อหาไฟล์ไม่ตรงกับชนิดรูปภาพ")
    folder = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{spec[0]}"
    with open(os.path.join(folder, name), "wb") as f:
        f.write(data)
    _delete_avatar_file(user)
    user.avatar_path = name
    db.commit()
    return ok({"avatar_url": _avatar_url(user)})


@router.delete("/me/avatar")
def delete_avatar(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _delete_avatar_file(user)
    user.avatar_path = None
    db.commit()
    return ok({"avatar_url": None})


@router.get("/{username}")
def public_profile(username: str, db: Session = Depends(get_db)):
    """Public profile: no email, hash, tokens or internal data."""
    u = db.scalar(select(User).where(func.lower(User.username) == username.lower()))
    if not u:
        raise AppError(404, "ไม่พบผู้ใช้")
    return ok({"username": u.username, "display_name": u.display_name, "bio": u.bio,
               "avatar_url": _avatar_url(u), "created_at": u.created_at.isoformat()})
