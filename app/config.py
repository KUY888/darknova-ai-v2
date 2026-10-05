import os
from dotenv import load_dotenv

load_dotenv()


def _b(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes")


class Settings:
    APP_NAME = "DARKNOVA AI"
    VERSION = "V2"
    DEVELOPER = "KUY888 (คุณลีโอ)"
    APP_TYPE = "AI Assistant"
    COMMUNITY = "DARKNOVA COMMUNITY"
    DISCORD = "https://discord.gg/E4gp2jSg3F"
    ABOUT = ("DARKNOVA AI คือ AI Assistant ที่พัฒนาโดย KUY888 (คุณลีโอ) สำหรับการสนทนา "
             "การเขียนโค้ด การ Debug และการวางแผนโปรเจกต์ โดยออกแบบให้สามารถพัฒนาต่อเป็น "
             "AI Platform ได้ในอนาคต")

    def __init__(self) -> None:
        self.AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()
        self.AI_MODEL = os.getenv("AI_MODEL", "")
        self.AI_API_KEY = os.getenv("AI_API_KEY", "")
        self.AI_BASE_URL = os.getenv("AI_BASE_URL", "")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./darknova.db")
        self.SECRET_KEY = os.getenv("SECRET_KEY", "")
        self.TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
        self.RATE_LIMIT = _b("RATE_LIMIT_ENABLED", "true")
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
        self.GITHUB_URL = os.getenv("GITHUB_URL", "")


settings = Settings()
