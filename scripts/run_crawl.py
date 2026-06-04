import argparse

from app.db import SessionLocal, init_db
from app.services.crawler_source import crawl_public_notices
from app.services.ingest import ingest_tender


def main(limit: int = 10) -> int:
    init_db()
    notices = []

    try:
        notices = crawl_public_notices(limit=limit)
    except Exception as exc:
        print(f"crawl list failed: {exc}")
        return 0

    inserted_count = 0
    with SessionLocal() as session:
        for notice in notices:
            created = ingest_tender(session, notice)
            if created is not None:
                inserted_count += 1

    print(f"crawl complete: inserted {inserted_count} notices")
    return inserted_count


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl real public tender notices")
    parser.add_argument("--limit", type=int, default=10, help="maximum notices to ingest")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(limit=args.limit)
