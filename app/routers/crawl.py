from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/crawl")


@router.post("/run")
def run_crawl(request: Request) -> RedirectResponse:
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/opportunities", status_code=303)
