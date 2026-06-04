from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
def login(
    request: Request, username: str = Form(...), password: str = Form(...)
) -> RedirectResponse:
    if username == "admin" and password == "admin123":
        request.session["user"] = {"username": "admin"}
        return RedirectResponse("/opportunities", status_code=303)
    return RedirectResponse("/login", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
