# Enterprise Whitelist Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Guangdong-focused enterprise whitelist layer that tags, boosts, and filters opportunities from priority groups like 中建、华润、京基、星河、万科、招商、保利、城投、水务集团 without bypassing the existing A-class product match gate.

**Architecture:** Keep the current single-app FastAPI structure and add one focused service for whitelist detection plus a small scoring enhancement path. Persist focus-account metadata on `Opportunity`, expose it through repositories and templates, and keep ingestion order strict: A-class product match first, focus-account detection second, ranking boost third.

**Tech Stack:** Python 3.9+, FastAPI, SQLAlchemy, SQLite, Jinja2, pytest

---

## File Structure Map

- `app/config.py` - add priority enterprise whitelist defaults and focus score config
- `app/db.py` - add lightweight SQLite column bootstrap for new opportunity fields
- `app/models.py` - add focus-account columns to `Opportunity`
- `app/repositories.py` - add filtered/sorted opportunity queries and focus-only list support
- `app/services/focus_accounts.py` - detect enterprise names and groups from buyer/title/content
- `app/services/scorer.py` - add focus-account bonus after A-class gate passes
- `app/services/ingest.py` - persist focus metadata and enforce new scoring flow
- `app/routers/opportunities.py` - support `focus_only` list filter
- `app/templates/opportunities/list.html` - show focus tags and filter toggle
- `app/templates/opportunities/detail.html` - show detected focus company and group
- `scripts/run_crawl.py` - keep insert count tied to post-filter opportunities
- `tests/test_focus_accounts.py` - whitelist detection tests
- `tests/test_scoring.py` - scoring bonus tests
- `tests/test_ingest.py` - ingest persistence tests for focus metadata
- `tests/test_opportunity_routes.py` - list filter and template rendering tests

## Task 1: Add Enterprise Whitelist Detection Service

**Files:**
- Modify: `app/config.py`
- Create: `app/services/focus_accounts.py`
- Test: `tests/test_focus_accounts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_focus_accounts.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_focus_accounts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.focus_accounts'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/config.py
import os


class Settings:
    app_name: str = "Water Sector Business Opportunity Radar"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./radar.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    focus_account_bonus: int = int(os.getenv("FOCUS_ACCOUNT_BONUS", "20"))
    focus_account_groups: dict[str, tuple[str, ...]] = {
        "中建系": ("中建", "中国建筑", "中建八局", "中建三局"),
        "华润系": ("华润", "华润置地", "华润万象生活"),
        "京基": ("京基",),
        "星河": ("星河", "星河控股"),
        "万科": ("万科",),
        "招商": ("招商", "招商蛇口"),
        "保利": ("保利", "保利发展"),
        "城投": ("城投", "城市投资", "城市建设投资"),
        "水务集团": ("水务集团", "水务投资", "供水集团"),
    }


settings = Settings()
```

```python
# app/services/focus_accounts.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_focus_accounts.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add app/config.py app/services/focus_accounts.py tests/test_focus_accounts.py
git commit -m "feat: add enterprise whitelist detection"
```

## Task 2: Persist Focus Metadata on Opportunities

**Files:**
- Modify: `app/db.py`
- Modify: `app/models.py`
- Modify: `app/services/ingest.py`
- Test: `tests/test_ingest.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_ingest.py
def test_ingest_tender_persists_focus_account_metadata() -> None:
    init_db()
    detail = {
        "source": "fixture-source",
        "source_url": "https://example.com/focus-1",
        "title": "华润置地深圳项目消防水箱采购公告",
        "city": "深圳",
        "publish_date": None,
        "deadline": None,
        "buyer_name": "华润置地（深圳）发展有限公司",
        "agency_name": None,
        "budget_amount": None,
        "content": "项目采购消防水箱及安装服务",
    }

    with SessionLocal() as session:
        session.query(Opportunity).delete()
        session.query(Tender).delete()
        session.query(Keyword).delete()
        session.commit()
        session.add(Keyword(word="消防水箱", category="A", weight=35, enabled=True))
        session.commit()

        created = ingest_tender(session, detail)

        assert created is not None
        assert created.is_focus_account is True
        assert created.focus_company_group == "华润系"
        assert "重点客户" in created.reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_ingest.py::test_ingest_tender_persists_focus_account_metadata -v`
Expected: FAIL with `AttributeError` for missing `is_focus_account` or missing focus detection

- [ ] **Step 3: Write minimal implementation**

```python
# app/models.py
class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id"), unique=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(1), default="D")
    reason: Mapped[str] = mapped_column(Text, default="")
    matched_keywords: Mapped[str] = mapped_column(Text, default="[]")
    follow_status: Mapped[str] = mapped_column(String(50), default="新发现")
    owner_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_focus_account: Mapped[bool] = mapped_column(Boolean, default=False)
    focus_company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    focus_company_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    focus_match_field: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tender: Mapped["Tender"] = relationship()
```

```python
# app/db.py
from sqlalchemy import text


def _ensure_opportunity_focus_columns() -> None:
    columns = {
        "is_focus_account": "INTEGER DEFAULT 0",
        "focus_company_name": "VARCHAR(255)",
        "focus_company_group": "VARCHAR(100)",
        "focus_match_field": "VARCHAR(50)",
    }
    with engine.begin() as connection:
        existing = {
            row[1] for row in connection.execute(text("PRAGMA table_info(opportunities)"))
        }
        for name, ddl in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE opportunities ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    from app.models import FollowLog, Keyword, Opportunity, Tender, User

    Base.metadata.create_all(bind=engine)
    _ensure_opportunity_focus_columns()
```

```python
# app/services/ingest.py
from app.services.focus_accounts import detect_focus_account


focus_result = detect_focus_account(tender_data)

opportunity.is_focus_account = focus_result["is_focus_account"]
opportunity.focus_company_name = focus_result["focus_company_name"]
opportunity.focus_company_group = focus_result["focus_company_group"]
opportunity.focus_match_field = focus_result["focus_match_field"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_ingest.py::test_ingest_tender_persists_focus_account_metadata -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/db.py app/models.py app/services/ingest.py tests/test_ingest.py
git commit -m "feat: persist focus account metadata on opportunities"
```

## Task 3: Add Focus Account Bonus to Scoring

**Files:**
- Modify: `app/services/scorer.py`
- Test: `tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_scoring.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_scoring.py::test_score_tender_adds_focus_account_bonus -v`
Expected: FAIL with `TypeError` because `focus_result` is not an accepted argument

- [ ] **Step 3: Write minimal implementation**

```python
# app/services/scorer.py
from app.config import settings


def score_tender(tender: dict, matches: list[dict], focus_result: dict | None = None) -> dict:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_scoring.py::test_score_tender_adds_focus_account_bonus -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/scorer.py tests/test_scoring.py
git commit -m "feat: add focus account score bonus"
```

## Task 4: Expose Focus Tags in Opportunity List and Detail

**Files:**
- Modify: `app/repositories.py`
- Modify: `app/routers/opportunities.py`
- Modify: `app/templates/opportunities/list.html`
- Modify: `app/templates/opportunities/detail.html`
- Test: `tests/test_opportunity_routes.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_opportunity_routes.py
def test_opportunity_list_can_filter_focus_accounts_only() -> None:
    client = TestClient(app)
    client.post("/login", data={"username": "admin", "password": "admin123"})

    with SessionLocal() as session:
        session.query(Opportunity).delete()
        session.query(Tender).delete()
        session.commit()
        focus_tender = Tender(
            source="fixture-source",
            source_url="https://example.com/focus-list",
            title="华润项目消防水箱采购公告",
            city="深圳",
            publish_date=None,
            deadline=None,
            buyer_name="华润置地（深圳）发展有限公司",
            agency_name=None,
            budget_amount=None,
            content="消防水箱采购",
            content_hash="focus-list",
        )
        normal_tender = Tender(
            source="fixture-source",
            source_url="https://example.com/normal-list",
            title="普通消防水箱采购公告",
            city="深圳",
            publish_date=None,
            deadline=None,
            buyer_name="深圳市某单位",
            agency_name=None,
            budget_amount=None,
            content="消防水箱采购",
            content_hash="normal-list",
        )
        session.add_all([focus_tender, normal_tender])
        session.flush()
        session.add(
            Opportunity(
                tender_id=focus_tender.id,
                score=80,
                level="A",
                reason="命中A类词:消防水箱，重点客户:华润系",
                matched_keywords="[]",
                is_focus_account=True,
                focus_company_name="华润置地（深圳）发展有限公司",
                focus_company_group="华润系",
                focus_match_field="buyer_name",
            )
        )
        session.add(
            Opportunity(
                tender_id=normal_tender.id,
                score=60,
                level="B",
                reason="命中A类词:消防水箱",
                matched_keywords="[]",
                is_focus_account=False,
            )
        )
        session.commit()

    response = client.get("/opportunities?focus_only=1")

    assert response.status_code == 200
    assert "华润项目消防水箱采购公告" in response.text
    assert "普通消防水箱采购公告" not in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_opportunity_routes.py::test_opportunity_list_can_filter_focus_accounts_only -v`
Expected: FAIL because route does not filter on `focus_only`

- [ ] **Step 3: Write minimal implementation**

```python
# app/repositories.py
def list_opportunities(session: Session, focus_only: bool = False) -> list[Opportunity]:
    stmt = (
        select(Opportunity)
        .options(joinedload(Opportunity.tender))
        .order_by(Opportunity.is_focus_account.desc(), Opportunity.score.desc(), Opportunity.created_at.desc())
    )
    if focus_only:
        stmt = stmt.where(Opportunity.is_focus_account.is_(True))
    return session.execute(stmt).scalars().all()
```

```python
# app/routers/opportunities.py
@router.get("", response_class=HTMLResponse)
def opportunity_list(request: Request, focus_only: int = 0):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    with SessionLocal() as session:
        items = list_opportunities(session, focus_only=bool(focus_only))

    return templates.TemplateResponse(
        request,
        "opportunities/list.html",
        {"items": items, "focus_only": bool(focus_only)},
    )
```

```html
<!-- app/templates/opportunities/list.html -->
<form method="get" action="/opportunities">
  <label>
    <input type="checkbox" name="focus_only" value="1" {% if focus_only %}checked{% endif %} />
    只看重点客户
  </label>
  <button type="submit">筛选</button>
</form>
{% for item in items %}
  <tr>
    <td>
      <a href="/opportunities/{{ item.id }}">{{ item.tender.title }}</a>
      {% if item.is_focus_account %}
      <span>[重点客户]</span>
      <span>{{ item.focus_company_group }}</span>
      {% endif %}
    </td>
  </tr>
{% endfor %}
```

```html
<!-- app/templates/opportunities/detail.html -->
{% if item.is_focus_account %}
<p>重点客户：{{ item.focus_company_group }}</p>
<p>命中公司：{{ item.focus_company_name }}</p>
<p>命中字段：{{ item.focus_match_field }}</p>
{% endif %}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_opportunity_routes.py::test_opportunity_list_can_filter_focus_accounts_only -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/repositories.py app/routers/opportunities.py app/templates/opportunities/list.html app/templates/opportunities/detail.html tests/test_opportunity_routes.py
git commit -m "feat: add focus account list filter"
```

## Task 5: Verify End-to-End Behavior in Current Crawl Flow

**Files:**
- Modify: `scripts/run_crawl.py`
- Test: `tests/test_ingest.py`
- Test: `tests/test_scoring.py`
- Test: `tests/test_opportunity_routes.py`

- [ ] **Step 1: Run focused regression for new whitelist behavior**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_focus_accounts.py tests/test_scoring.py tests/test_ingest.py tests/test_opportunity_routes.py -v`
Expected: PASS with all new whitelist-related tests green

- [ ] **Step 2: Reseed the active preview database with whitelist keywords**

Run: `DATABASE_URL=sqlite:///./real_crawl_verify.db PYTHONPATH=. .venv/bin/python scripts/seed_data.py`
Expected: `seed complete`

- [ ] **Step 3: Re-run crawl and observe filtered count**

Run: `DATABASE_URL=sqlite:///./real_crawl_verify.db PYTHONPATH=. .venv/bin/python scripts/run_crawl.py --limit 30`
Expected: command completes successfully and inserts only A-class matched opportunities, with focus-account rows sorted first if found

- [ ] **Step 4: Verify database contains focus metadata when matched**

```bash
python3 -c "import sqlite3; conn=sqlite3.connect('real_crawl_verify.db'); cur=conn.cursor(); print(cur.execute('select title, is_focus_account, focus_company_group from opportunities join tenders on tenders.id = opportunities.tender_id order by is_focus_account desc, score desc limit 10').fetchall()); conn.close()"
```

Expected: rows print successfully; focus-account rows show `1` and a non-empty group when matched

- [ ] **Step 5: Commit**

```bash
git add scripts/run_crawl.py
git commit -m "chore: verify enterprise whitelist crawl flow"
```

## Self-Review

- Spec coverage: this plan covers whitelist groups, focus-account detection, metadata persistence, score bonus, list/detail presentation, and filtered ranking without relaxing the A-class product gate.
- Placeholder scan: all tasks include exact files, tests, commands, and code snippets; no TODO/TBD markers remain.
- Type consistency: `detect_focus_account`, `focus_company_name`, `focus_company_group`, `focus_match_field`, `is_focus_account`, and `focus_account_bonus` are named consistently across config, ingest, scoring, repositories, and templates.
