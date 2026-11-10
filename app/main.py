from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import ROOT, settings
from app.routers import admin, admin_freelance, admin_photo, admin_resume, public

app = FastAPI(
    title="Portfolio",
    docs_url=None if settings.read_only else "/docs",
    redoc_url=None,
    openapi_url=None if settings.read_only else "/openapi.json",
)

if settings.admin_enabled:
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        same_site="lax",
        https_only=settings.session_https_only,
        max_age=60 * 60 * 8,
    )

# Na Vercel a CDN serve public/** direto; este mount cobre o desenvolvimento local.
# check_dir=False evita erro de startup se a pasta não estiver no bundle da função.
app.mount(
    "/static",
    StaticFiles(directory=ROOT / "public" / "static", check_dir=False),
    name="static",
)

app.include_router(public.router)

if settings.admin_enabled:
    app.include_router(admin.router)
    app.include_router(admin_freelance.router)
    app.include_router(admin_resume.router)
    app.include_router(admin_photo.router)


@app.get("/api/health", include_in_schema=False)
def health():
    return {"status": "ok"}
