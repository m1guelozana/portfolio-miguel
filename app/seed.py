from sqlalchemy import select

from app.database import SessionLocal
from app.models import Project, SiteSettings

PROJECTS = [
    {
        "slug": "psa-connect-auditoria",
        "title": "PSA-Connect Auditoria",
        "category": "Engenharia de dados",
        "summary": "Pipeline de auditoria do histórico de queries do Impala.",
        "stack": ["Python", "Impala", "Kerberos",
                  "Streamlit", "Pandas", "Hadoop"],
        "pipeline": ["Impala", "Python", "Tabela de log", "Dashboard"],
        "metrics": [{"label": "Execução", "value": "diária"}],
        "featured": True,
        "order": 1,
    },
    {
        "slug": "automacoes-juridicas",
        "title": "Automações jurídicas",
        "category": "Automação",
        "summary": "Scraping e automação de rotinas processuais.",
        "stack": ["Python", "Selenium"],
        "pipeline": ["Portal", "Selenium", "Parser", "Planilha"],
        "metrics": [],
        "featured": True,
        "order": 2,
    },
]


def run() -> None:
    with SessionLocal() as db:
        for data in PROJECTS:
            exists = db.scalar(select(Project).where(
              Project.slug == data["slug"]))
            if not exists:
                db.add(Project(**data))

        if db.get(SiteSettings, 1) is None:
            db.add(
                SiteSettings(
                    id=1,
                    hero_text=(
                        """Desenvolvedor full-stack com foco
                        em engenharia de dados e automações.
                        Pipelines, integrações
                        e ferramentas internas em Python."""
                    ),
                    hero_title="Miguel Ozana"
                )
            )
        db.commit()


if __name__ == "__main__":
    run()
