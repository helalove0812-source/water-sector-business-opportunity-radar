import os
from pathlib import Path


db_file = Path("test_radar.db")
if db_file.exists():
    db_file.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"


def pytest_sessionfinish() -> None:
    if db_file.exists():
        db_file.unlink()
