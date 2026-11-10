import os
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session  # noqa: F401  (mantido por consistência com os outros routers)

from app.auth import require_admin, verify_csrf
from app.resume import MAX_BYTES, RESUME_PATH, resume_exists
from app.routers.admin import redirect
from app.templating import templates

router = APIRouter(
    prefix="/admin/resume",
    include_in_schema=False,
    dependencies=[Depends(require_admin)],
)


def resume_info() -> dict | None:
    if not resume_exists():
        return None
    stat = RESUME_PATH.stat()
    return {
        "size_kb": max(1, round(stat.st_size / 1024)),
        "updated": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
    }


def render(
    request: Request,
    error: str | None = None,
    saved: bool = False,
    deleted: bool = False,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "admin/resume.html",
        {
            "info": resume_info(),
            "error": error,
            "saved": saved,
            "deleted": deleted,
            "max_mb": MAX_BYTES // (1024 * 1024),
        },
        status_code=status_code,
    )


@router.get("", response_class=HTMLResponse)
def resume_page(request: Request, saved: int = 0, deleted: int = 0):
    return render(request, saved=bool(saved), deleted=bool(deleted))


@router.post("", dependencies=[Depends(verify_csrf)])
async def resume_upload(request: Request):
    form = await request.form()
    upload = form.get("file")

    if upload is None or not getattr(upload, "filename", ""):
        return render(request, error="Selecione um arquivo PDF.", status_code=422)

    data = await upload.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        return render(
            request,
            error=f"Arquivo maior que {MAX_BYTES // (1024 * 1024)} MB.",
            status_code=422,
        )
    if not data.startswith(b"%PDF-"):
        return render(request, error="O arquivo não é um PDF válido.", status_code=422)

    tmp_path = None
    try:
        RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=RESUME_PATH.parent, suffix=".tmp")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_path, RESUME_PATH)  # troca atômica
    except OSError:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        return render(
            request,
            error="Não foi possível gravar o arquivo neste ambiente (disco somente leitura?).",
            status_code=500,
        )

    return redirect("/admin/resume?saved=1")


@router.post("/delete", dependencies=[Depends(verify_csrf)])
def resume_delete():
    try:
        RESUME_PATH.unlink(missing_ok=True)
    except OSError:
        pass
    return redirect("/admin/resume?deleted=1")
