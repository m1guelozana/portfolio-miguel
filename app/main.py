from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import admin, admin_freelance, admin_photo, admin_resume, public
from app.templating import BASE_DIR

app = FastAPI(title="Portfolio")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=settings.session_https_only,
    max_age=60 * 60 * 8,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(admin_freelance.router)
app.include_router(admin_resume.router)
app.include_router(admin_photo.router)


@app.get("/api/health", include_in_schema=False)
def health():
    return {"status": "ok"}