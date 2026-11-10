import re
import unicodedata
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    check_credentials,
    is_admin,
    require_admin,
    verify_csrf,
)
from app.database import get_db
from app.models import Project, SiteSettings
from app.templating import render_markdown, templates

router = APIRouter(prefix="/admin", include_in_schema=False)
protected = APIRouter(dependencies=[Depends(require_admin)])

CATEGORIES = ["Engenharia de dados", "Automação", "Full-stack"]
SETTINGS_FIELDS = ("name", "hero_title", "hero_text", "email", "github_url",
                   "linkedin_url")
PROJECT_FIELDS = (
    "title", "slug", "category", "summary", "description_md", "stack",
    "pipeline", "metrics", "repo_url", "demo_url", "cover_url",
    "featured", "published", "order",
)


# ---------- helpers ----------

def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii",
                                                      "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean_list(values) -> list[str]:
    return [str(v).strip() for v in values if str(v).strip()]


def empty_form() -> dict:
    return {
        "title": "", "slug": "", "category": CATEGORIES[0], "summary": "",
        "description_md": "", "stack": [], "pipeline": [], "metrics": [],
        "repo_url": "", "demo_url": "", "cover_url": "",
        "featured": False, "published": True, "order": 0,
    }


def form_from_project(project: Project) -> dict:
    return {f: getattr(project, f) for f in PROJECT_FIELDS}


async def project_payload(request: Request) -> dict:
    form = await request.form()
    title = str(form.get("title", "")).strip()
    slug = slugify(str(form.get("slug", "")).strip() or title)
    try:
        order = int(form.get("order") or 0)
    except ValueError:
        order = 0

    metrics = [
        {"label": str(label).strip(), "value": str(value).strip()}
        for label, value in zip(form.getlist("metric_label"),
                                form.getlist("metric_value"))
        if str(label).strip() and str(value).strip()
    ]

    return {
        "title": title,
        "slug": slug,
        "category": str(form.get("category", "")).strip() or CATEGORIES[0],
        "summary": str(form.get("summary", "")).strip(),
        "description_md": str(form.get("description_md", "")),
        "stack": clean_list(str(form.get("stack", "")).split(",")),
        "pipeline": clean_list(form.getlist("pipeline")),
        "metrics": metrics,
        "repo_url": str(form.get("repo_url", "")).strip() or None,
        "demo_url": str(form.get("demo_url", "")).strip() or None,
        "cover_url": str(form.get("cover_url", "")).strip() or None,
        "featured": form.get("featured") == "on",
        "published": form.get("published") == "on",
        "order": order,
    }


def validate(db: Session,
             data: dict, current_id: int | None = None) -> str | None:
    if not data["title"]:
        return "Informe o título."
    if not data["summary"]:
        return "Informe o resumo."
    if not data["slug"]:
        return "Slug inválido."
    clash = db.scalar(select(Project).where(Project.slug == data["slug"]))
    if clash and clash.id != current_id:
        return "Já existe um projeto com esse slug."
    return None


def render_form(
    request: Request,
    form: dict,
    project_id: int | None = None,
    error: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "admin/project_form.html",
        {
            "form": form,
            "project_id": project_id,
            "error": error,
            "categories": CATEGORIES,
        },
        status_code=status_code,
    )


def get_site(db: Session) -> SiteSettings:
    site = db.get(SiteSettings, 1)
    if site is None:
        site = SiteSettings(id=1)
        db.add(site)
        db.commit()
    return site


def stack_to_text(groups: list | None) -> str:
    """[{"group": "Dados", "items": ["Python", "SQL"]}]
    -> "Dados: Python, SQL" por linha."""
    return "\n".join(
        f"{g.get('group', '')}: {', '.join(g.get('items', []))}"
        for g in (groups or [])
    )


def parse_stack(text: str) -> list[dict]:
    groups = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        group, items = line.split(":", 1)
        items_list = clean_list(items.split(","))
        if group.strip() and items_list:
            groups.append({"group": group.strip(), "items": items_list})
    return groups


# ---------- auth (público) ----------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if is_admin(request):
        return redirect("/admin/")
    return templates.TemplateResponse(request, "admin/login.html",
                                      {"error": None})


@router.post("/login", dependencies=[Depends(verify_csrf)])
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    if check_credentials(username, password):
        request.session.clear()  # sessão nova após o login
        request.session["admin"] = True
        return redirect("/admin/")
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"error": "Usuário ou senha inválidos."},
        status_code=401,
    )


# ---------- protegido ----------

@protected.post("/logout", dependencies=[Depends(verify_csrf)])
def logout(request: Request):
    request.session.clear()
    return redirect("/admin/login")


@protected.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    projects = db.scalars(
      select(Project).order_by(Project.order, Project.id)).all()
    return templates.TemplateResponse(
        request, "admin/project_list.html", {"projects": projects}
    )


@protected.get("/projects/new", response_class=HTMLResponse)
def project_new_page(request: Request):
    return render_form(request, empty_form())


@protected.post("/projects/new", dependencies=[Depends(verify_csrf)])
async def project_create(
    request: Request,
    data: Annotated[dict, Depends(project_payload)],
    db: Session = Depends(get_db),
):
    error = validate(db, data)
    if error:
        return render_form(request, data, None, error, status_code=422)
    db.add(Project(**data))
    db.commit()
    return redirect("/admin/")


@protected.get("/projects/{project_id}", response_class=HTMLResponse)
def project_edit_page(
    request: Request, project_id: int, db: Session = Depends(get_db)
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return render_form(request, form_from_project(project), project_id)


@protected.post("/projects/{project_id}", dependencies=[Depends(verify_csrf)])
async def project_update(
    request: Request,
    project_id: int,
    data: Annotated[dict, Depends(project_payload)],
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    error = validate(db, data, current_id=project_id)
    if error:
        return render_form(request, data, project_id, error, status_code=422)
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()
    return redirect("/admin/")


@protected.post("/projects/{project_id}/delete",
                dependencies=[Depends(verify_csrf)])
def project_delete(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is not None:
        db.delete(project)
        db.commit()
    return redirect("/admin/")


@protected.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, saved: int = 0,
                  db: Session = Depends(get_db)):
    site = get_site(db)
    return templates.TemplateResponse(
        request,
        "admin/settings.html",
        {
            "site": site,
            "saved": bool(saved),
            "stack_text": stack_to_text(site.stack_groups),
            "experience": site.experience or [],
        },
    )


@protected.post("/settings", dependencies=[Depends(verify_csrf)])
async def settings_update(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    site = get_site(db)

    for field in SETTINGS_FIELDS:
        setattr(site, field, str(form.get(field, "")).strip())

    site.stack_groups = parse_stack(str(form.get("stack_text", "")))

    site.experience = [
        {
            "role": str(role).strip(),
            "company": str(company).strip(),
            "period": str(period).strip(),
            "description": str(description).strip(),
        }
        for role, company, period, description in zip(
            form.getlist("exp_role"),
            form.getlist("exp_company"),
            form.getlist("exp_period"),
            form.getlist("exp_description"),
        )
        if str(role).strip() or str(company).strip()
    ]

    db.commit()
    return redirect("/admin/settings?saved=1")


# ---------- fragmentos HTMX ----------

@protected.get("/partials/step", response_class=HTMLResponse)
def partial_step(request: Request):
    return templates.TemplateResponse(
        request, "admin/partials/step_row.html", {"step_value": ""}
    )


@protected.get("/partials/metric", response_class=HTMLResponse)
def partial_metric(request: Request):
    return templates.TemplateResponse(
        request, "admin/partials/metric_row.html", {"m_label": "",
                                                    "m_value": ""}
    )


@protected.get("/partials/experience", response_class=HTMLResponse)
def partial_experience(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/partials/experience_row.html",
        {"e_role": "", "e_company": "", "e_period": "", "e_description": ""},
    )


@protected.post("/preview", response_class=HTMLResponse)
def preview(description_md: Annotated[str, Form()] = ""):
    return HTMLResponse(render_markdown(description_md))


router.include_router(protected)
