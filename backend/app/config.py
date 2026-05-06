from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str
    db_path: str = "./data/ehr.db"
    app_env: str = "local"
    log_level: str = "INFO"

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""


settings = Settings()
