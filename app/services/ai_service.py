from sqlalchemy.orm import Session
from app.config import settings
from app.database import utcnow
from app.errors import AppError
from app.models.conversation import Conversation
from app.models.message import Message
from app.providers import ProviderError, get_provider

BASE_PROMPT = f"""คุณคือ DARKNOVA AI V2 ผู้ช่วย AI ที่พัฒนาโดย {settings.DEVELOPER}
หลักการ: วิเคราะห์ก่อนตอบ ตอบตรงประเด็น ไม่แต่งข้อมูล หากไม่แน่ใจให้บอกว่าไม่แน่ใจ
ช่วยเรื่อง Coding, Debug, วางแผน, ตรวจ Logic/Syntax และอธิบายสาเหตุของปัญหาก่อนแก้
ห้ามอ้างว่าได้รันโค้ดหรือเข้าถึงไฟล์ เว้นแต่ระบบทำจริง
ห้ามช่วย: malware, credential theft, phishing, account takeover, data theft, โจมตีระบบของผู้อื่น
ช่วยได้: defensive security, secure coding, security testing ในระบบที่ได้รับอนุญาต, วิเคราะห์ log, hardening
ถ้าถูกถามว่าใครเป็นผู้พัฒนา ให้ตอบ: "ผู้พัฒนาคือ {settings.DEVELOPER}"
ถ้าถูกถามช่องทางติดต่อ ให้ตอบ: "{settings.COMMUNITY}: {settings.DISCORD}" """

MODE_PROMPTS = {
    "CHAT": "โหมด CHAT: สนทนาและตอบคำถามทั่วไป",
    "CODE": "โหมด CODE: สร้างและแก้ไขโค้ดให้ถูกต้อง รันได้จริง พร้อมอธิบายสั้น ๆ",
    "DEBUG": "โหมด DEBUG: วิเคราะห์ Syntax, Runtime, Logic และ Dependency error อธิบายสาเหตุก่อนเสนอวิธีแก้",
    "PLAN": "โหมด PLAN: วางแผนโครงสร้างและขั้นตอนก่อนลงมือสร้าง",
}
HISTORY_LIMIT = 20


def respond(db: Session, conv: Conversation, content: str, mode: str | None = None) -> Message:
    """Call the provider with conversation history, persist user + assistant messages."""
    if mode:
        conv.mode = mode
    history = [{"role": m.role, "content": m.content} for m in conv.messages[-HISTORY_LIMIT:]]
    msgs = [{"role": "system", "content": BASE_PROMPT + "\n" + MODE_PROMPTS[conv.mode]},
            *history, {"role": "user", "content": content}]
    try:
        provider = get_provider()
        if not provider.is_configured():
            raise AppError(503, "ยังไม่ได้ตั้งค่า AI Provider (AI_API_KEY)")
        reply = provider.chat(msgs)
    except ProviderError:
        raise AppError(502, "AI Provider ตอบกลับไม่สำเร็จ กรุณาลองใหม่")
    except ValueError as exc:
        raise AppError(503, str(exc))
    db.add(Message(conversation_id=conv.id, role="user", content=content))
    assistant = Message(conversation_id=conv.id, role="assistant", content=reply)
    db.add(assistant)
    conv.updated_at = utcnow()
    db.commit()
    db.refresh(assistant)
    return assistant
