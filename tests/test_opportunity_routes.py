from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models import FollowLog, Opportunity, Tender


def login(client: TestClient) -> None:
    client.post("/login", data={"username": "admin", "password": "admin123"})


def clear_opportunities() -> None:
    with SessionLocal() as session:
        session.execute(delete(FollowLog))
        session.execute(delete(Opportunity))
        session.execute(delete(Tender))
        session.commit()


def seed_opportunity() -> Opportunity:
    with SessionLocal() as session:
        tender = Tender(
            source="fixture-source",
            source_url="https://example.com/opportunity-1",
            title="深圳市某医院不锈钢水箱采购项目",
            city="深圳",
            content="采购内容包含不锈钢水箱安装与配套服务",
            content_hash="hash-opportunity-1",
        )
        session.add(tender)
        session.flush()

        opportunity = Opportunity(
            tender_id=tender.id,
            score=60,
            level="B",
            reason="命中A类词:不锈钢水箱; 重点地区:深圳",
        )
        session.add(opportunity)
        session.commit()
        session.refresh(opportunity)
        return opportunity


def test_opportunity_list_requires_login() -> None:
    client = TestClient(app)

    response = client.get("/opportunities", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_opportunity_list_shows_seeded_rows_after_login() -> None:
    clear_opportunities()
    client = TestClient(app)

    try:
        opportunity = seed_opportunity()
        login(client)

        response = client.get("/opportunities")

        assert response.status_code == 200
        assert "深圳市某医院不锈钢水箱采购项目" in response.text
        assert "深圳" in response.text
        assert "60" in response.text
        assert "B" in response.text
        assert f"/opportunities/{opportunity.id}" in response.text
    finally:
        clear_opportunities()


def test_opportunity_detail_shows_reason_content_and_follow_form() -> None:
    clear_opportunities()
    client = TestClient(app)

    try:
        opportunity = seed_opportunity()
        login(client)

        response = client.get(f"/opportunities/{opportunity.id}")

        assert response.status_code == 200
        assert "命中A类词:不锈钢水箱; 重点地区:深圳" in response.text
        assert "采购内容包含不锈钢水箱安装与配套服务" in response.text
        assert f"/opportunities/{opportunity.id}/follow" in response.text
        assert "保存跟进备注" in response.text
    finally:
        clear_opportunities()


def test_follow_note_requires_login() -> None:
    clear_opportunities()
    client = TestClient(app)

    try:
        opportunity = seed_opportunity()

        response = client.post(
            f"/opportunities/{opportunity.id}/follow",
            data={"note": "今日已电话联系客户"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/login"
    finally:
        clear_opportunities()


def test_follow_note_redirects_to_detail_and_persists_log() -> None:
    clear_opportunities()
    client = TestClient(app)

    try:
        opportunity = seed_opportunity()
        login(client)

        response = client.post(
            f"/opportunities/{opportunity.id}/follow",
            data={"note": "今日已电话联系客户"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == f"/opportunities/{opportunity.id}"

        with SessionLocal() as session:
            follow_log = session.execute(
                select(FollowLog).where(FollowLog.opportunity_id == opportunity.id)
            ).scalar_one()

        assert follow_log.note == "今日已电话联系客户"
        assert follow_log.created_by == "admin"
    finally:
        clear_opportunities()


def test_manual_crawl_endpoint_redirects_back_to_list_after_login() -> None:
    client = TestClient(app)
    login(client)

    response = client.post("/crawl/run", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/opportunities"
