from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: int | None = None
    mode: str | None = Field(default=None, pattern=r"^(CHAT|CODE|DEBUG|PLAN)$")
