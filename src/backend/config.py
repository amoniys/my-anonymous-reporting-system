import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Anonymous Reporting System"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_secret_key_for_demo")
    SERVER_COUNT: int = 3  # 模拟洋葱路由经过的服务器数量

settings = Settings()