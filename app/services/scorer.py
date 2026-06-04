from datetime import datetime


PRIORITY_CITIES = {"深圳", "广州", "东莞", "惠州", "佛山", "珠海", "中山"}


def score_tender(tender: dict, matches: list[dict]) -> dict:
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
