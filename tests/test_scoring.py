from datetime import datetime, timedelta

from app.services.matcher import match_keywords
from app.services.scorer import score_tender


def test_score_tender_for_strong_keyword_and_region() -> None:
    keywords = [
        {"word": "不锈钢水箱", "category": "A", "weight": 35},
        {"word": "安装", "category": "B", "weight": 15},
    ]
    tender = {
        "title": "深圳市某医院不锈钢水箱采购安装项目",
        "content": "项目内容包含不锈钢水箱和安装服务",
        "city": "深圳",
        "deadline": datetime.utcnow() + timedelta(days=3),
    }

    matches = match_keywords(tender, keywords)
    score = score_tender(tender, matches)

    assert [item["word"] for item in matches] == ["不锈钢水箱", "安装"]
    assert score["level"] in {"A", "S"}
    assert "深圳" in score["reason"]
    assert "截止时间未过期" in score["reason"]


def test_score_tender_does_not_add_bonus_for_expired_non_priority_city() -> None:
    keywords = [{"word": "泵站", "category": "D", "weight": 15}]
    tender = {
        "title": "某污水处理厂泵站维修项目",
        "content": "本项目涉及泵站维修。",
        "city": "南宁",
        "deadline": datetime.utcnow() - timedelta(days=1),
    }

    matches = match_keywords(tender, keywords)
    score = score_tender(tender, matches)

    assert [item["word"] for item in matches] == ["泵站"]
    assert score["score"] == 15
    assert score["level"] == "D"
    assert "重点地区" not in score["reason"]
    assert "截止时间未过期" not in score["reason"]


def test_score_tender_adds_focus_account_bonus() -> None:
    tender = {
        "title": "华润项目消防水箱采购安装公告",
        "content": "消防水箱安装",
        "city": "深圳",
        "deadline": datetime.utcnow() + timedelta(days=2),
    }
    matches = [{"word": "消防水箱", "category": "A", "weight": 35}]
    focus_result = {
        "is_focus_account": True,
        "focus_company_name": "华润置地（深圳）发展有限公司",
        "focus_company_group": "华润系",
        "focus_match_field": "title",
    }

    result = score_tender(tender, matches, focus_result=focus_result)

    assert result["score"] == 80
    assert result["level"] == "A"
    assert "重点客户:华润系" in result["reason"]
