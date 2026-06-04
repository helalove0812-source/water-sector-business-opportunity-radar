from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import Keyword


def login(client: TestClient) -> None:
    client.post("/login", data={"username": "admin", "password": "admin123"})


def clear_keywords() -> None:
    with SessionLocal() as session:
        session.execute(delete(Keyword))
        session.commit()


def test_create_keyword_and_show_in_list() -> None:
    clear_keywords()
    client = TestClient(app)
    try:
        login(client)

        response = client.post(
            "/keywords",
            data={"word": "一体化泵站", "category": "A", "weight": "35", "enabled": "on"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert "一体化泵站" in response.text
    finally:
        clear_keywords()
