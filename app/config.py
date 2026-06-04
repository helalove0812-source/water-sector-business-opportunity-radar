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
