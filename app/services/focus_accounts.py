from app.config import settings


def detect_focus_account(tender: dict) -> dict:
    candidates = [
        ("buyer_name", tender.get("buyer_name") or ""),
        ("title", tender.get("title") or ""),
        ("content", tender.get("content") or ""),
    ]

    for group, aliases in settings.focus_account_groups.items():
        for field_name, value in candidates:
            for alias in aliases:
                if alias and alias in value:
                    return {
                        "is_focus_account": True,
                        "focus_company_name": value,
                        "focus_company_group": group,
                        "focus_match_field": field_name,
                    }

    return {
        "is_focus_account": False,
        "focus_company_name": None,
        "focus_company_group": None,
        "focus_match_field": None,
    }
