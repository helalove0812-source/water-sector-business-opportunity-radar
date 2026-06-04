from fastapi.testclient import TestClient

from app.main import app


def test_login_page_loads() -> None:
    client = TestClient(app)

    response = client.get("/login")

    assert response.status_code == 200
    assert "登录" in response.text


def test_valid_login_redirects_to_opportunities() -> None:
    client = TestClient(app)

    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/opportunities"
