import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.auth import require_admin, verify_csrf
from app.photo import MAX_BYTES, PHOTO_PATH, SIZE, photo_url, process_photo
from app.routers.admin import redirect
from app.templating import templates

router = APIRouter(
    prefix="/admin/photo",
    include_in_schema=False,
    dependencies=[Depends(require_admin)],
)


def render(
    request: Request,
    error: str | None = None,
    saved: bool = False,
    deleted: bool = False,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "admin/photo.html",
        {
            "url": photo_url(),
            "error": error,
            "saved": saved,
            "deleted": deleted,
            "max_mb": MAX_BYTES // (1024 * 1024),
            "size": SIZE,
        },
        status_code=status_code,
    )


@router.get("", response_class=HTMLResponse)
def photo_page(request: Request, saved: int = 0, deleted: int = 0):
    return render(request, saved=bool(saved), deleted=bool(deleted))


@router.post("", dependencies=[Depends(verify_csrf)])
async def photo_upload(request: Request):
    form = await request.form()
    upload = form.get("file")

    if upload is None or not getattr(upload, "filename", ""):
        return render(request, error="Selecione uma imagem.", status_code=422)

    data = await upload.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        return render(
            request,
            error=f"Arquivo maior que {MAX_BYTES // (1024 * 1024)} MB.",
            status_code=422,
        )

    try:
        processed = process_photo(data)
    except ValueError:
        return render(
            request,
            error="Imagem inválida ou formato não suportado (use JPG, PNG ou WebP).",
            status_code=422,
        )

    tmp_path = None
    try:
        PHOTO_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=PHOTO_PATH.parent, suffix=".tmp")
        with os.fdopen(fd, "wb") as f:
            f.write(processed)
        os.replace(tmp_path, PHOTO_PATH)  # troca atômica
    except OSError:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        return render(
            request,
            error="Não foi possível gravar o arquivo neste ambiente (disco somente leitura?).",
            status_code=500,
        )

    return redirect("/admin/photo?saved=1")


@router.post("/delete", dependencies=[Depends(verify_csrf)])
def photo_delete():
    try:
        PHOTO_PATH.unlink(missing_ok=True)
    except OSError:
        pass
    return redirect("/admin/photo?deleted=1")