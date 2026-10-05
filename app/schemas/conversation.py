from pydantic import BaseModel, Field

MODE_PATTERN = r"^(CHAT|CODE|DEBUG|PLAN)$"


class ConversationCreate(BaseModel):
    title: str = Field(default="New Chat", min_length=1, max_length=120)
    mode: str = Field(default="CHAT", pattern=MODE_PATTERN)


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    mode: str | None = Field(default=None, pattern=MODE_PATTERN)
