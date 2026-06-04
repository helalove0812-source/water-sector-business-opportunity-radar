from pathlib import Path

from sqlalchemy import func, select

from app.db import SessionLocal, init_db
from app.models import Keyword, Opportunity, Tender
from app.services.crawler_source import parse_detail_html, parse_list_html
from app.services.ingest import ingest_tender
from scripts.run_crawl import main as run_crawl_main


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


def test_run_crawl_main_fetches_real_source_and_skips_failed_details(monkeypatch) -> None:
    init_db()

    list_html = """
    <html>
      <body>
        <ul>
          <li><a href="/doc_5106.html">项目一公开招标公告 2026-06-02 项目一公开招标公告 采购公告 256人查看</a></li>
          <li><a href="/doc_5105.html">项目二竞争性磋商公告 2026-06-01 项目二竞争性磋商公告 采购公告 20人查看</a></li>
        </ul>
      </body>
    </html>
    """
    detail_html = """
    <html>
      <body>
        <div class="content">
          <h2>东莞市二次供水设备采购项目公开招标公告</h2>
          <div>采购公告</div>
          <div>来源：原创</div>
          <div>2026-06-01 10:00:00</div>
          <p>和盛咨询（广东）有限公司受东莞市某单位委托，开展东莞市二次供水设备采购项目。</p>
          <p>采购预算：人民币560,000.00元</p>
          <p>响应文件提交截止时间：2026年06月08日 09时30分</p>
        </div>
      </body>
    </html>
    """

    def fake_fetch_html(url: str, timeout: float = 20.0) -> str:
        if url == "http://www.hscgfw.com/":
            return list_html
        if url == "http://www.hscgfw.com/doc_5106.html":
            return detail_html
        if url == "http://www.hscgfw.com/doc_5105.html":
            raise RuntimeError("502 Bad Gateway")
        raise AssertionError(url)

    with SessionLocal() as session:
        session.query(Opportunity).delete()
        session.query(Tender).delete()
        session.query(Keyword).delete()
        session.commit()
        session.add(Keyword(word="二次供水", category="B", weight=15, enabled=True))
        session.commit()

    monkeypatch.setattr("app.services.crawler_source.fetch_html", fake_fetch_html)

    inserted_count = run_crawl_main()

    with SessionLocal() as session:
        tender_count = session.execute(select(func.count(Tender.id))).scalar_one()
        opportunity = session.execute(select(Opportunity)).scalar_one()
        tender = session.execute(select(Tender)).scalar_one()

        assert inserted_count == 1
        assert tender_count == 1
        assert opportunity.tender_id == tender.id
        assert tender.source == "hscgfw"
        assert tender.title == "东莞市二次供水设备采购项目公开招标公告"
