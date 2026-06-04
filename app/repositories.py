from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Keyword


def list_keywords(session: Session) -> list[Keyword]:
    return session.execute(
        select(Keyword).order_by(Keyword.created_at.desc())
    ).scalars().all()


def create_keyword(
    session: Session, word: str, category: str, weight: int, enabled: bool
) -> Keyword:
    keyword = Keyword(word=word, category=category, weight=weight, enabled=enabled)
    session.add(keyword)
    session.commit()
    session.refresh(keyword)
    return keyword
