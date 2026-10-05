import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from app import models  # noqa: F401  (register tables)
from app.config import settings
from app.database import Base, engine
from app.errors import AppError
from app.routes import auth, chat, conversations, system, users

log = logging.getLogger("darknova")
HERE = os.path.dirname(__file__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if len(settings.SECRET_KEY) < 16:
        raise RuntimeError("SECRET_KEY must be set (16+ chars). Generate: python -c \"import secrets;print(secrets.token_urlsafe(48))\"")
    Base.metadata.create_all(engine)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "avatars"), exist_ok=True)
    yield


app = FastAPI(title="DARKNOVA AI V2", version="2.0.0", lifespan=lifespan)


@app.get("/.well-known/assetlinks.json", include_in_schema=False)
async def assetlinks():
    return [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.kuy888.darknovaai",
                "sha256_cert_fingerprints": [
                    "REPLACE_WITH_RELEASE_SHA256"
                ],
            },
        }
    ]
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


def _err(status: int, msg: str) -> JSONResponse:
    return JSONResponse({"success": False, "error": msg}, status_code=status)


@app.exception_handler(AppError)
async def _app_error(_: Request, e: AppError):
    return _err(e.status, e.message)


@app.exception_handler(StarletteHTTPException)
async def _http_error(_: Request, e: StarletteHTTPException):
    return _err(e.status_code, "ไม่พบหน้าที่ร้องขอ" if e.status_code == 404 else str(e.detail))


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, e: RequestValidationError):
    first = e.errors()[0] if e.errors() else {}
    field = ".".join(str(x) for x in first.get("loc", [])[1:])
    return _err(422, f"ข้อมูลไม่ถูกต้อง: {field} {first.get('msg', '')}".strip())


@app.exception_handler(Exception)
async def _unhandled(_: Request, e: Exception):
    log.exception("Unhandled error")
    return _err(500, "เกิดข้อผิดพลาดภายในระบบ")


for r in (system.router, auth.router, users.router, conversations.router, chat.router):
    app.include_router(r)

os.makedirs(os.path.join(settings.UPLOAD_DIR, "avatars"), exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


@app.get("/app-profile", include_in_schema=False)
def app_profile_page():
    return FileResponse(os.path.join(HERE, "static", "app-profile.html"))


@app.get("/", include_in_schema=False)
def index_page():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


@app.get("/manifest.webmanifest", include_in_schema=False)
def pwa_manifest():
    return FileResponse(os.path.join(HERE, "static", "manifest.webmanifest"), media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def pwa_service_worker():
    # Served from "/" so the worker can control the whole app scope.
    return FileResponse(os.path.join(HERE, "static", "sw.js"), media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})
