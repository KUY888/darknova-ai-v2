from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,30}$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(default="", max_length=50)


class LoginIn(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)  # username or email
    password: str = Field(min_length=1, max_length=72)
