from app.auth import hash_password
from app.db import SessionLocal, init_db
from app.models import Keyword, User


DEFAULT_KEYWORDS = [
    ("不锈钢水箱", "A", 35),
    ("消防水箱", "A", 35),
    ("二次供水", "B", 15),
    ("隔油器", "D", 15),
]


def main() -> None:
    init_db()
    with SessionLocal() as session:
        if session.query(User).filter_by(username="admin").first() is None:
            session.add(
                User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role="admin",
                )
            )

        for word, category, weight in DEFAULT_KEYWORDS:
            if session.query(Keyword).filter_by(word=word).first() is None:
                session.add(
                    Keyword(
                        word=word,
                        category=category,
                        weight=weight,
                        enabled=True,
                    )
                )

        session.commit()

    print("seed complete")


if __name__ == "__main__":
    main()
