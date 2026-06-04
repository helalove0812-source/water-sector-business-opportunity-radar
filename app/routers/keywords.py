from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import is_logged_in
from app.db import SessionLocal
from app.repositories import create_keyword, list_keywords

router = APIRouter(prefix="/keywords")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def keyword_list(request: Request):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    with SessionLocal() as session:
        keywords = list_keywords(session)
    return templates.TemplateResponse(
        request,
        "keywords/list.html",
        {"keywords": keywords},
    )


@router.post("")
def keyword_create(
    request: Request,
    word: str = Form(...),
    category: str = Form(...),
    weight: int = Form(...),
    enabled: Optional[str] = Form(default=None),
) -> RedirectResponse:
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    with SessionLocal() as session:
        create_keyword(
            session,
            word=word,
            category=category,
            weight=weight,
            enabled=bool(enabled),
        )
    return RedirectResponse("/keywords", status_code=303)
