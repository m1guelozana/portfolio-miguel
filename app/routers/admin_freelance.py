from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import require_admin, verify_csrf
from app.database import get_db
from app.routers.admin import clean_list, get_site, redirect
from app.templating import templates

router = APIRouter(
    prefix="/admin/freelance",
    include_in_schema=False,
    dependencies=[Depends(require_admin)],
)


@router.get("", response_class=HTMLResponse)
def freelance_page(request: Request, saved: int = 0, db: Session = Depends(get_db)):
    site = get_site(db)
    return templates.TemplateResponse(
        request,
        "admin/freelance.html",
        {"site": site, "saved": bool(saved), "services": site.services or []},
    )


@router.post("", dependencies=[Depends(verify_csrf)])
async def freelance_update(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    site = get_site(db)

    site.freelance_enabled = form.get("freelance_enabled") == "on"
    site.freelance_title = str(form.get("freelance_title", "")).strip()
    site.freelance_text = str(form.get("freelance_text", "")).strip()
    site.freelance_contact_url = str(form.get("freelance_contact_url", "")).strip()

    site.services = [
        {
            "title": str(title).strip(),
            "description": str(description).strip(),
            "tags": clean_list(str(tags).split(",")),
        }
        for title, description, tags in zip(
            form.getlist("svc_title"),
            form.getlist("svc_description"),
            form.getlist("svc_tags"),
        )
        if str(title).strip()
    ]

    db.commit()
    return redirect("/admin/freelance?saved=1")


@router.get("/partials/service", response_class=HTMLResponse)
def partial_service(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/partials/service_row.html",
        {"svc_title": "", "svc_description": "", "svc_tags": ""},
    )
