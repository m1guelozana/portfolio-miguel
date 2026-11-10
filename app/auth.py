import secrets

import bcrypt
from fastapi import HTTPException, Request, status

from app.config import settings


def check_credentials(username: str, password: str) -> bool:
    user_ok = secrets.compare_digest(
        username.encode(), settings.admin_user.encode()
    )
    hashed = settings.admin_password_hash.encode()
    if not hashed:
        return False
    try:
        pass_ok = bcrypt.checkpw(password.encode(), hashed)
    except ValueError:
        pass_ok = False
    return user_ok and pass_ok


def is_admin(request: Request) -> bool:
    return bool(request.session.get("admin"))


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


async def verify_csrf(request: Request) -> None:
    form = await request.form()
    sent = str(form.get("csrf_token", ""))
    expected = request.session.get("csrf", "")
    if not expected or not secrets.compare_digest(sent.encode(),
                                                  expected.encode()):
        raise HTTPException(status_code=403, detail="Token CSRF inválido")
