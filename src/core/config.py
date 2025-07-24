# In src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    POSTGRES_DSN: str 
    REDIS_URL: str
    GEMINI_API_KEY: str

    WHATSAPP_ACCESS_TOKEN: str
    PHONE_NUMBER_ID: str
    WHATSAPP_VERIFY_TOKEN: str

# Create a single, reusable instance of the settings
settings = Settings()