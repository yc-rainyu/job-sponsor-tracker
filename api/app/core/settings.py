from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo root .env, so uv run works from any folder (containers use env vars)
ENV_FILE = Path(__file__).resolve().parents[3] / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra='ignore')

    database_url: str
    app_env: str = 'dev'
    jwt_secret: str = ''
    version: str = '0.1.0'
    search_trading_threshold: float = 0.8
    search_word_threshold: float = 0.6
    search_fuzzy_threshold: float = 0.3
    search_rate_limit_per_minute: int = 60
    analyse_rate_limit_per_minute: int = 20


settings = Settings()
