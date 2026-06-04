from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import Keyword


def test_init_db_creates_tables() -> None:
    init_db()

    with SessionLocal() as session:
        session.add(Keyword(word="不锈钢水箱", category="A", weight=35, enabled=True))
        session.commit()

        result = session.execute(select(Keyword)).scalar_one()

    assert result.word == "不锈钢水箱"
