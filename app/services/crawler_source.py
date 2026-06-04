import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


HSCGFW_BASE_URL = "http://www.hscgfw.com/"
CITY_NAMES = ("深圳", "广州", "东莞", "惠州", "佛山", "珠海", "中山")
EXCLUDED_NOTICE_KEYWORDS = ("结果公告", "中标", "成交", "更正公告")


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


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

    normalized = _normalize_text(value)
    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y年%m月%d日 %H时%M分",
        "%Y年%m月%d日",
    ):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def _extract_hscgfw_title(text: str) -> str:
    normalized = _normalize_text(text)
    match = re.match(r"^(.*?)\s+\d{4}-\d{2}-\d{2}\b", normalized)
    if match:
        return match.group(1).strip()
    return normalized


def _is_hscgfw_notice(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized or "公告" not in normalized:
        return False
    return not any(keyword in normalized for keyword in EXCLUDED_NOTICE_KEYWORDS)


def _extract_city(text: str) -> Optional[str]:
    for city in CITY_NAMES:
        if city in text:
            return city
    return None


def _extract_first_match(pattern: str, text: str) -> Optional[str]:
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def fetch_html(url: str, timeout: float = 20.0) -> str:
    response = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.text


def parse_list_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    fixture_links = soup.select("a.notice-link")
    if fixture_links:
        return [
            {
                "title": link.get_text(strip=True),
                "source_url": link["href"],
                "source": "fixture-source",
            }
            for link in fixture_links
        ]

    items = []
    seen_urls = set()
    for link in soup.select('a[href*="doc_"]'):
        href = link.get("href")
        if not href:
            continue
        absolute_url = urljoin(HSCGFW_BASE_URL, href)
        if absolute_url in seen_urls:
            continue

        text = _normalize_text(link.get_text(" ", strip=True))
        if not _is_hscgfw_notice(text):
            continue

        seen_urls.add(absolute_url)
        items.append(
            {
                "title": _extract_hscgfw_title(text),
                "source_url": absolute_url,
                "source": "hscgfw",
            }
        )
    return items


def parse_detail_html(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    fixture_title = soup.select_one("h1")
    if fixture_title and soup.select(".meta"):
        return {
            "source": "fixture-source",
            "source_url": source_url,
            "title": fixture_title.get_text(strip=True),
            "city": _parse_meta_value(soup, "地区"),
            "publish_date": _parse_date(_parse_meta_value(soup, "发布时间")),
            "deadline": _parse_date(_parse_meta_value(soup, "截止时间")),
            "buyer_name": None,
            "agency_name": None,
            "budget_amount": None,
            "content": soup.select_one(".content").get_text(strip=True),
        }

    content_root = soup.select_one(".content") or soup
    content_text = _normalize_text(content_root.get_text(" ", strip=True))
    title_node = content_root.select_one("h1") or content_root.select_one("h2")
    title = title_node.get_text(strip=True) if title_node else _extract_hscgfw_title(content_text)
    publish_date = _parse_date(_extract_first_match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", content_text))
    deadline = _parse_date(
        _extract_first_match(
            r"(?:截止时间|响应文件提交截止时间|投标截止时间)[：:\s]*"
            r"(\d{4}年\d{2}月\d{2}日\s*\d{2}时\d{2}分|\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2})?)",
            content_text,
        )
    )

    return {
        "source": "hscgfw",
        "source_url": source_url,
        "title": title,
        "city": _extract_city(title) or _extract_city(content_text),
        "publish_date": publish_date,
        "deadline": deadline,
        "buyer_name": _extract_first_match(r"受(.+?)(?:（以下简称[“\"]?采购人[”\"]?）|委托)", content_text),
        "agency_name": _extract_first_match(r"([^\s，。,；;（）()]+咨询（广东）有限公司)", content_text),
        "budget_amount": _extract_first_match(r"(?:采购预算|预算金额)[：:\s]*(?:人民币)?([0-9,]+(?:\.\d+)?)元", content_text),
        "content": content_text,
    }


def crawl_public_notices(limit: int = 10) -> list[dict]:
    list_html = fetch_html(HSCGFW_BASE_URL)
    items = parse_list_html(list_html)
    notices = []

    for item in items[:limit]:
        try:
            detail_html = fetch_html(item["source_url"])
        except Exception:
            continue
        notices.append(parse_detail_html(detail_html, item["source_url"]))

    return notices
