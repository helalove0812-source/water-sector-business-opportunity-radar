import hashlib
import json
from typing import Optional

from sqlalchemy import select

from app.models import Keyword, Opportunity, Tender
from app.services.focus_accounts import detect_focus_account
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


def _has_required_a_match(matches: list[dict]) -> bool:
    return any(item.get("category") == "A" for item in matches)


def ingest_tender(session, tender_data: dict) -> Optional[Opportunity]:
    keywords = session.execute(
        select(Keyword).where(Keyword.enabled.is_(True))
    ).scalars().all()
    keyword_dicts = [
        {"word": item.word, "category": item.category, "weight": item.weight}
        for item in keywords
    ]
    matches = match_keywords(tender_data, keyword_dicts)
    if not _has_required_a_match(matches):
        return None

    focus_result = detect_focus_account(tender_data)
    result = score_tender(tender_data, matches, focus_result=focus_result)
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
    opportunity.is_focus_account = focus_result["is_focus_account"]
    opportunity.focus_company_name = focus_result["focus_company_name"]
    opportunity.focus_company_group = focus_result["focus_company_group"]
    opportunity.focus_match_field = focus_result["focus_match_field"]

    session.commit()
    session.refresh(opportunity)
    return opportunity
