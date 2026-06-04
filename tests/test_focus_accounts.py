from app.services.focus_accounts import detect_focus_account


def test_detect_focus_account_from_buyer_name() -> None:
    tender = {
        "title": "深圳某项目消防水箱采购公告",
        "buyer_name": "华润置地（深圳）发展有限公司",
        "content": "采购消防水箱设备",
    }

    result = detect_focus_account(tender)

    assert result == {
        "is_focus_account": True,
        "focus_company_name": "华润置地（深圳）发展有限公司",
        "focus_company_group": "华润系",
        "focus_match_field": "buyer_name",
    }


def test_detect_focus_account_matches_all_whitelist_groups() -> None:
    cases = [
        ("中建八局华南建设有限公司", "中建系"),
        ("华润置地（深圳）发展有限公司", "华润系"),
        ("京基地产集团有限公司", "京基"),
        ("深圳市星河房地产开发有限公司", "星河"),
        ("万科企业股份有限公司", "万科"),
        ("招商蛇口产业园发展有限公司", "招商"),
        ("保利发展控股集团股份有限公司", "保利"),
        ("深圳市城市建设投资发展有限公司", "城投"),
        ("深圳市水务集团有限公司", "水务集团"),
    ]

    for buyer_name, expected_group in cases:
        result = detect_focus_account(
            {
                "title": "广东重点项目供水设备采购公告",
                "buyer_name": buyer_name,
                "content": "采购水务设备",
            }
        )

        assert result["is_focus_account"] is True
        assert result["focus_company_name"] == buyer_name
        assert result["focus_company_group"] == expected_group
        assert result["focus_match_field"] == "buyer_name"


def test_detect_focus_account_returns_false_for_non_whitelist_company() -> None:
    tender = {
        "title": "深圳某项目消防水箱采购公告",
        "buyer_name": "深圳市某普通机电公司",
        "content": "采购消防水箱设备",
    }

    result = detect_focus_account(tender)

    assert result == {
        "is_focus_account": False,
        "focus_company_name": None,
        "focus_company_group": None,
        "focus_match_field": None,
    }
