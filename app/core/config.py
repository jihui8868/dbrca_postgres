import os
from functools import lru_cache
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: SecretStr
    database: str = "information_schema"
    error_log_path: str = "/var/log/mysql/error.log"
    connect_timeout: int = 5


class LLMConfig(BaseModel):
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com/v1"
    api_key: SecretStr
    temperature: float = 0.0
    max_tokens: int = 8192
    timeout: int = 3600


class LangSmithConfig(BaseModel):
    enabled: bool = False
    api_key: SecretStr = SecretStr("")
    project: str = "dbrca-postgres"
    endpoint: str = "https://api.smith.langchain.com"


class AgentConfig(BaseModel):
    max_iterations: int = 50
    session_ttl_seconds: int = 3600


class AppConfig(BaseModel):
    title: str = "Postgres RCA Agent"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8888
    log_level: str = "INFO"

class LogConfig(BaseModel):
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", case_sensitive=False)

    # 项目信息
    PROJECT_NAME: str = "Postgres RCA"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = ["*"]

    # 数据库配置
    postgres: DatabaseConfig
    llm: LLMConfig
    langsmith: LangSmithConfig = LangSmithConfig()
    agent: AgentConfig = AgentConfig()
    app: AppConfig = AppConfig()
    log: LogConfig = LogConfig()




@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
