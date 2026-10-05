from fastapi import APIRouter
from sqlalchemy import text
from app.config import settings
from app.database import engine
from app.errors import ok
from app.providers import get_provider

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return ok({"status": "ok"})


def _db_ok() -> bool:
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get("/system/status")
def status():
    try:
        p = get_provider()
        # Reports whether the provider is configured; it does NOT make a live upstream call.
        ai_online, provider, model = p.is_configured(), p.name, p.model
    except ValueError:
        ai_online, provider, model = False, settings.AI_PROVIDER, ""
    f = lambda b: "online" if b else "offline"  # noqa: E731
    return ok({"api": "online", "database": f(_db_ok()), "ai": f(ai_online),
               "ai_provider": provider, "ai_model": model})


@router.get("/system/about")
def about():
    try:
        p = get_provider()
        provider, model = p.name, p.model
    except ValueError:
        provider, model = settings.AI_PROVIDER, ""
    return ok({"app_name": settings.APP_NAME, "version": settings.VERSION, "app_type": settings.APP_TYPE,
               "developer": settings.DEVELOPER, "community": settings.COMMUNITY, "discord": settings.DISCORD,
               "github": settings.GITHUB_URL or None, "about": settings.ABOUT,
               "ai_provider": provider, "ai_model": model, "logo_url": "/static/logo.jpg"})
