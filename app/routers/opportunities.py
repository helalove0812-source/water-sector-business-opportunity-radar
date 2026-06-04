from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import is_logged_in
from app.db import SessionLocal
from app.repositories import (
    add_follow_log,
    get_opportunity,
    list_follow_logs,
    list_opportunities,
)

router = APIRouter(prefix="/opportunities")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def opportunity_list(request: Request, focus_only: bool = False):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    with SessionLocal() as session:
        items = list_opportunities(session, focus_only=focus_only)

    return templates.TemplateResponse(
        request,
        "opportunities/list.html",
        {"items": items, "focus_only": focus_only},
    )


@router.get("/{opportunity_id}", response_class=HTMLResponse)
def opportunity_detail(request: Request, opportunity_id: int):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    with SessionLocal() as session:
        item = get_opportunity(session, opportunity_id)
        logs = list_follow_logs(session, opportunity_id)

    return templates.TemplateResponse(
        request,
        "opportunities/detail.html",
        {"item": item, "logs": logs},
    )


@router.post("/{opportunity_id}/follow")
def opportunity_follow(
    request: Request,
    opportunity_id: int,
    note: str = Form(...),
):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    with SessionLocal() as session:
        add_follow_log(
            session,
            opportunity_id=opportunity_id,
            note=note,
            created_by=request.session["user"]["username"],
        )

    return RedirectResponse(f"/opportunities/{opportunity_id}", status_code=303)
