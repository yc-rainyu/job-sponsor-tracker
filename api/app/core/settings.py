from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

    database_url: str
    app_env: str = 'dev'
    jwt_secret: str = ''
    version: str = '0.0.1'
    search_trading_threshold: float = 0.8
    search_word_threshold: float = 0.6
    search_fuzzy_threshold: float = 0.3

    search_rate_limit_per_minute: int = 60


settings = Settings()
