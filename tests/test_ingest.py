from pathlib import Path

from sqlalchemy import func, select

from app.db import SessionLocal, init_db
from app.models import Keyword, Opportunity, Tender
from app.services.crawler_source import parse_detail_html, parse_list_html
from app.services.ingest import ingest_tender


def test_fixture_parsers_return_normalized_tender_payload() -> None:
    list_html = Path("tests/fixtures/source/list.html").read_text(encoding="utf-8")
    detail_html = Path("tests/fixtures/source/detail.html").read_text(encoding="utf-8")

    items = parse_list_html(list_html)

    assert items == [
        {
            "title": "深圳市某医院不锈钢水箱采购项目",
            "source_url": "https://example.com/tender-1",
            "source": "fixture-source",
        }
    ]

    detail = parse_detail_html(detail_html, items[0]["source_url"])

    assert detail["title"] == items[0]["title"]
    assert detail["source_url"] == items[0]["source_url"]
    assert detail["source"] == "fixture-source"
    assert detail["city"] == "深圳"
    assert detail["content"] == "采购内容包含不锈钢水箱安装与配套服务"


def test_ingest_tender_deduplicates_tender_and_creates_single_opportunity() -> None:
    init_db()
    detail_html = Path("tests/fixtures/source/detail.html").read_text(encoding="utf-8")
    detail = parse_detail_html(detail_html, "https://example.com/tender-1")

    with SessionLocal() as session:
        session.query(Opportunity).delete()
        session.query(Tender).delete()
        session.query(Keyword).delete()
        session.commit()

        try:
            session.add(Keyword(word="不锈钢水箱", category="A", weight=35, enabled=True))
            session.commit()

            first = ingest_tender(session, detail)
            second = ingest_tender(session, detail)

            tender_count = session.execute(select(func.count(Tender.id))).scalar_one()
            opportunity_count = session.execute(select(func.count(Opportunity.id))).scalar_one()

            assert first.tender_id == second.tender_id
            assert tender_count == 1
            assert opportunity_count == 1
            assert second.score == 60
            assert second.level == "B"
            assert "命中A类词:不锈钢水箱" in second.reason
            assert "重点地区:深圳" in second.reason
        finally:
            session.query(Opportunity).delete()
            session.query(Tender).delete()
            session.query(Keyword).delete()
            session.commit()
