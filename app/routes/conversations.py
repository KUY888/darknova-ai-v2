from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.errors import AppError, RateLimiter, ok
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import MessageIn
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.security.auth import get_current_user
from app.services import ai_service

router = APIRouter(prefix="/conversations", tags=["conversations"])
chat_limit = RateLimiter(30, 60)


def conv_out(c: Conversation) -> dict:
    return {"id": c.id, "title": c.title, "mode": c.mode,
            "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat()}


def msg_out(m: Message) -> dict:
    return {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}


def owned(db: Session, user: User, conv_id: int) -> Conversation:
    """Ownership check; returns 404 for other users' conversations (no existence leak)."""
    c = db.get(Conversation, conv_id)
    if not c or c.user_id != user.id:
        raise AppError(404, "ไม่พบบทสนทนา")
    return c


@router.get("")
def list_conversations(q: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Conversation).where(Conversation.user_id == user.id)
    if q:
        like = f"%{q}%"
        in_msgs = select(Message.conversation_id).where(Message.content.ilike(like))
        stmt = stmt.where(or_(Conversation.title.ilike(like), Conversation.id.in_(in_msgs)))
    rows = db.scalars(stmt.order_by(Conversation.updated_at.desc())).all()
    return ok([conv_out(c) for c in rows])


@router.post("", status_code=201)
def create_conversation(body: ConversationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = Conversation(user_id=user.id, title=body.title, mode=body.mode)
    db.add(c)
    db.commit()
    return ok(conv_out(c))


@router.get("/{conv_id}")
def get_conversation(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(conv_out(owned(db, user, conv_id)))


@router.patch("/{conv_id}")
def update_conversation(conv_id: int, body: ConversationUpdate, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    c = owned(db, user, conv_id)
    if body.title is not None:
        c.title = body.title
    if body.mode is not None:
        c.mode = body.mode
    db.commit()
    return ok(conv_out(c))


@router.delete("/{conv_id}")
def delete_conversation(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(owned(db, user, conv_id))
    db.commit()
    return ok({"deleted": conv_id})


@router.get("/{conv_id}/messages")
def list_messages(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok([msg_out(m) for m in owned(db, user, conv_id).messages])


@router.post("/{conv_id}/messages", dependencies=[Depends(chat_limit)])
def send_message(conv_id: int, body: MessageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = owned(db, user, conv_id)
    if c.title == "New Chat":
        c.title = body.content[:60]
    return ok(msg_out(ai_service.respond(db, c, body.content)))
