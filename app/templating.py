from pathlib import Path

import markdown
from fastapi.templating import Jinja2Templates

from app.auth import csrf_token
from app.photo import photo_url
from app.resume import resume_exists

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def render_markdown(text: str) -> str:
    return markdown.markdown(text or "", extensions=["fenced_code", "tables"])


templates.env.globals["csrf_token"] = csrf_token
templates.env.globals["has_resume"] = resume_exists
templates.env.globals["photo_url"] = photo_url
templates.env.filters["md"] = render_markdown
