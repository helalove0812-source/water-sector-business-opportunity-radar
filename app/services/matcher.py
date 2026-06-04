def match_keywords(tender: dict, keywords: list[dict]) -> list[dict]:
    haystack_title = tender.get("title", "")
    haystack_content = tender.get("content", "")
    matched = []

    for keyword in keywords:
        word = keyword["word"]
        if word in haystack_title or word in haystack_content:
            matched.append(keyword)

    return matched
