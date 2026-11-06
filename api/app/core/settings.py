from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# repo root .env, so uv run works from any folder (containers use env vars)
ENV_FILE = Path(__file__).resolve().parents[3] / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, extra='ignore', hide_input_in_errors=True
    )

    database_url: str
    app_env: str = 'dev'
    jwt_secret: str = ''
    google_client_id: str = ''
    proxy_key: str = ''
    version: str = '0.1.0'
    search_trading_threshold: float = 0.8
    search_word_threshold: float = 0.6
    search_fuzzy_threshold: float = 0.3
    search_rate_limit_per_minute: int = 60
    analyse_rate_limit_per_minute: int = 20
    demo_rate_limit_per_hour: int = 5

    @model_validator(mode='after')
    def _check_jwt_secret(self) -> Self:
        # an empty or short key would let anyone forge session cookies
        if self.app_env == 'prod' and len(self.jwt_secret) < 32:
            raise ValueError(
                'JWT_SECRET must be at least 32 characters when APP_ENV=prod'
            )
        return self


settings = Settings()
