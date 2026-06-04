from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def _ensure_opportunity_focus_columns() -> None:
    columns = {
        "is_focus_account": "INTEGER DEFAULT 0",
        "focus_company_name": "VARCHAR(255)",
        "focus_company_group": "VARCHAR(100)",
        "focus_match_field": "VARCHAR(50)",
    }
    with engine.begin() as connection:
        existing = {
            row[1] for row in connection.execute(text("PRAGMA table_info(opportunities)"))
        }
        for name, ddl in columns.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE opportunities ADD COLUMN {name} {ddl}")
                )


def init_db() -> None:
    from app.models import FollowLog, Keyword, Opportunity, Tender, User

    Base.metadata.create_all(bind=engine)
    _ensure_opportunity_focus_columns()
