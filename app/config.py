import os


class Settings:
    app_name: str = "Water Sector Business Opportunity Radar"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./radar.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")


settings = Settings()
