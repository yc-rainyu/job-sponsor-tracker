from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

    database_url: str
    app_env: str = 'dev'
    jwt_secret: str = ''
    version: str = '0.0.1'


settings = Settings()
