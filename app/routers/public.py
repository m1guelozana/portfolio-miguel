from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, SiteSettings
from app.photo import PHOTO_PATH
from app.resume import DOWNLOAD_NAME, RESUME_PATH, resume_exists
from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    projects = db.scalars(
        select(Project)
        .where(Project.published.is_(True))
        .order_by(Project.order, Project.id)
    ).all()
    site = db.get(SiteSettings, 1)
    return templates.TemplateResponse(
        request, "index.html", {"projects": projects, "site": site}
    )


@router.get("/freelance", response_class=HTMLResponse)
def freelance(request: Request, db: Session = Depends(get_db)):
    site = db.get(SiteSettings, 1)
    if site is None or not site.freelance_enabled:
        raise HTTPException(status_code=404, detail="Página não encontrada")
    return templates.TemplateResponse(request, "freelance.html", {"site": site})


@router.get("/curriculo")
def resume():
    if not resume_exists():
        raise HTTPException(status_code=404, detail="Currículo não disponível")
    return FileResponse(
        RESUME_PATH,
        media_type="application/pdf",
        filename=DOWNLOAD_NAME,  # força o download com esse nome
    )


@router.get("/foto")
def photo():
    if not PHOTO_PATH.is_file():
        raise HTTPException(status_code=404, detail="Foto não disponível")
    return FileResponse(
        PHOTO_PATH,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/projects/{slug}", response_class=HTMLResponse)
def project_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    project = db.scalar(
        select(Project).where(Project.slug == slug, Project.published.is_(True))
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    site = db.get(SiteSettings, 1)
    return templates.TemplateResponse(
        request, "project_detail.html", {"project": project, "site": site}
    )