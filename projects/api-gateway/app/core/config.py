from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Hunter API Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL 配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "job_hunter"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here"  # 在生产环境中应该从环境变量获取
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # etcd 配置
    ETCD_HOST: str = "localhost"
    ETCD_PORT: int = 2379

    class Config:
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )


settings = Settings()
