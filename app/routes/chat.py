from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.conversation import Conversation
from app.models.user import User
from app.routes.conversations import chat_limit, conv_out, msg_out, owned
from app.schemas.chat import ChatIn
from app.security.auth import get_current_user
from app.services import ai_service
from app.errors import ok

router = APIRouter(tags=["chat"])


@router.post("/chat", dependencies=[Depends(chat_limit)])
def chat(body: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a message; creates a new conversation when conversation_id is omitted."""
    if body.conversation_id is not None:
        conv = owned(db, user, body.conversation_id)
    else:
        conv = Conversation(user_id=user.id, title=body.message[:60], mode=body.mode or "CHAT")
        db.add(conv)
        db.commit()
    reply = ai_service.respond(db, conv, body.message, body.mode)
    return ok({"conversation": conv_out(conv), "reply": msg_out(reply)})
