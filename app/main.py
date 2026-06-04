from fastapi import FastAPI

from app.config import settings
from app.db import init_db

app = FastAPI(title=settings.app_name)
init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
