from pathlib import Path

from app.db import SessionLocal, init_db
from app.services.crawler_source import parse_detail_html, parse_list_html
from app.services.ingest import ingest_tender


def main() -> None:
    init_db()

    list_html = Path("tests/fixtures/source/list.html").read_text(encoding="utf-8")
    detail_html = Path("tests/fixtures/source/detail.html").read_text(encoding="utf-8")
    items = parse_list_html(list_html)

    with SessionLocal() as session:
        for item in items:
            detail = parse_detail_html(detail_html, item["source_url"])
            ingest_tender(session, detail)

    print("crawl complete")


if __name__ == "__main__":
    main()
