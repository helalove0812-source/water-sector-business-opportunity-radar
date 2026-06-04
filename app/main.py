from fastapi import FastAPI

app = FastAPI(title="Water Sector Business Opportunity Radar")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
