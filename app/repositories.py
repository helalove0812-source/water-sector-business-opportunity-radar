from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import FollowLog, Keyword, Opportunity


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


def list_opportunities(
    session: Session, *, focus_only: bool = False
) -> list[Opportunity]:
    stmt = (
        select(Opportunity)
        .options(joinedload(Opportunity.tender))
        .order_by(
            Opportunity.is_focus_account.desc(),
            Opportunity.score.desc(),
            Opportunity.created_at.desc(),
        )
    )
    if focus_only:
        stmt = stmt.where(Opportunity.is_focus_account.is_(True))

    return (
        session.execute(stmt)
        .scalars()
        .all()
    )


def get_opportunity(session: Session, opportunity_id: int) -> Opportunity:
    return session.execute(
        select(Opportunity)
        .options(joinedload(Opportunity.tender))
        .where(Opportunity.id == opportunity_id)
    ).scalar_one()


def list_follow_logs(session: Session, opportunity_id: int) -> list[FollowLog]:
    return (
        session.execute(
            select(FollowLog)
            .where(FollowLog.opportunity_id == opportunity_id)
            .order_by(FollowLog.created_at.desc())
        )
        .scalars()
        .all()
    )


def add_follow_log(
    session: Session, opportunity_id: int, note: str, created_by: str
) -> FollowLog:
    row = FollowLog(
        opportunity_id=opportunity_id,
        note=note,
        created_by=created_by,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
