from sqlalchemy import JSON, Boolean, Integer, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(400))
    description_md: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), index=True)

    stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    # lista de etapas: ["Impala", "Python", "Tabela de log", "Dashboard"]
    pipeline: Mapped[list[str]] = mapped_column(JSON, default=list)
    # lista de {"label": "...", "value": "..."}
    metrics: Mapped[list[dict]] = mapped_column(JSON, default=list)

    repo_url: Mapped[str | None] = mapped_column(String(300), default=None)
    demo_url: Mapped[str | None] = mapped_column(String(300), default=None)
    cover_url: Mapped[str | None] = mapped_column(String(300), default=None)

    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0, index=True)


class SiteSettings(Base):
    """Linha única (id=1) com o conteúdo geral do site."""

    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Miguel Ozana")
    hero_title: Mapped[str] = mapped_column(String(200), default="Miguel Ozana")
    hero_text: Mapped[str] = mapped_column(Text, default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    github_url: Mapped[str] = mapped_column(String(300), default="")
    linkedin_url: Mapped[str] = mapped_column(String(300), default="")

    # [{"group": "Dados", "items": ["Python", "SQL"]}]
    stack_groups: Mapped[list] = mapped_column(
        JSON, default=list, server_default="[]"
    )
    # [{"role": "...", "company": "...", "period": "...", "description": "..."}]
    experience: Mapped[list] = mapped_column(
        JSON, default=list, server_default="[]"
    )

    # --- freelance ---
    freelance_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    freelance_title: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    freelance_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    freelance_contact_url: Mapped[str] = mapped_column(
        String(300), default="", server_default=""
    )
    # [{"title": "...", "description": "...", "tags": ["Python", "Selenium"]}]
    services: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")