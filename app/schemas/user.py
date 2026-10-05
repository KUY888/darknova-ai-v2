from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    username: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_]{3,30}$")
    display_name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=300)
