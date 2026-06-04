from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import init_db
from app.routers import auth, crawl, keywords, opportunities

app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(auth.router)
app.include_router(crawl.router)
app.include_router(keywords.router)
app.include_router(opportunities.router)
init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
