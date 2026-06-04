import hashlib
import json

from sqlalchemy import select

from app.models import Keyword, Opportunity, Tender
from app.services.matcher import match_keywords
from app.services.scorer import score_tender


def _build_content_hash(tender_data: dict) -> str:
    payload = "|".join(
        [
            tender_data["title"],
            tender_data["source"],
            tender_data["source_url"],
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ingest_tender(session, tender_data: dict) -> Opportunity:
    tender = session.execute(
        select(Tender).where(Tender.source_url == tender_data["source_url"])
    ).scalar_one_or_none()
    content_hash = _build_content_hash(tender_data)

    if tender is None:
        tender = Tender(**tender_data, content_hash=content_hash)
        session.add(tender)
        session.flush()
    else:
        for field, value in tender_data.items():
            setattr(tender, field, value)
        tender.content_hash = content_hash
        session.flush()

    keywords = session.execute(
        select(Keyword).where(Keyword.enabled.is_(True))
    ).scalars().all()
    keyword_dicts = [
        {"word": item.word, "category": item.category, "weight": item.weight}
        for item in keywords
    ]
    matches = match_keywords(tender_data, keyword_dicts)
    result = score_tender(tender_data, matches)

    opportunity = session.execute(
        select(Opportunity).where(Opportunity.tender_id == tender.id)
    ).scalar_one_or_none()
    if opportunity is None:
        opportunity = Opportunity(tender_id=tender.id)
        session.add(opportunity)

    opportunity.score = result["score"]
    opportunity.level = result["level"]
    opportunity.reason = result["reason"]
    opportunity.matched_keywords = json.dumps(matches, ensure_ascii=False)

    session.commit()
    session.refresh(opportunity)
    return opportunity
