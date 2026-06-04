from datetime import datetime
from typing import Optional

from app.config import settings


PRIORITY_CITIES = {"深圳", "广州", "东莞", "惠州", "佛山", "珠海", "中山"}


def score_tender(
    tender: dict, matches: list[dict], focus_result: Optional[dict] = None
) -> dict:
    score = 0
    reasons = []

    for item in matches:
        category = item.get("category")
        if category == "A":
            score += 35
            reasons.append(f"命中A类词:{item['word']}")
        elif category == "B":
            score += 15
            reasons.append(f"命中B类词:{item['word']}")
        elif category == "D":
            score += 15
            reasons.append(f"命中D类词:{item['word']}")

    city = tender.get("city")
    if city in PRIORITY_CITIES:
        score += 15
        reasons.append(f"重点地区:{city}")

    deadline = tender.get("deadline")
    if deadline and deadline > datetime.utcnow():
        score += 10
        reasons.append("截止时间未过期")

    if focus_result and focus_result.get("is_focus_account"):
        score += settings.focus_account_bonus
        reasons.append(f"重点客户:{focus_result['focus_company_group']}")

    score = min(score, 100)
    if score >= 90:
        level = "S"
    elif score >= 75:
        level = "A"
    elif score >= 60:
        level = "B"
    elif score >= 40:
        level = "C"
    else:
        level = "D"

    return {"score": score, "level": level, "reason": "，".join(reasons)}
