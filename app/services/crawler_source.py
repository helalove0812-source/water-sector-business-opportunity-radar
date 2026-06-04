from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup


def _parse_meta_value(html: BeautifulSoup, label: str) -> Optional[str]:
    for node in html.select(".meta"):
        text = node.get_text(strip=True)
        prefix = f"{label}："
        if text.startswith(prefix):
            return text.removeprefix(prefix).strip()
    return None


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


def parse_list_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for link in soup.select("a.notice-link"):
        items.append(
            {
                "title": link.get_text(strip=True),
                "source_url": link["href"],
                "source": "fixture-source",
            }
        )
    return items


def parse_detail_html(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    return {
        "source": "fixture-source",
        "source_url": source_url,
        "title": soup.select_one("h1").get_text(strip=True),
        "city": _parse_meta_value(soup, "地区"),
        "publish_date": _parse_date(_parse_meta_value(soup, "发布时间")),
        "deadline": _parse_date(_parse_meta_value(soup, "截止时间")),
        "buyer_name": None,
        "agency_name": None,
        "budget_amount": None,
        "content": soup.select_one(".content").get_text(strip=True),
    }
