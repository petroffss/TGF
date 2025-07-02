import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Telegram API
    TELEGRAM_API_ID: Optional[str] = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH: Optional[str] = os.getenv("TELEGRAM_API_HASH")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    JWT_SECRET: Optional[str] = os.getenv("JWT_SECRET")

    # Email settings for alerts
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER")
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    ALERT_EMAIL: Optional[str] = os.getenv("ALERT_EMAIL")

    # Grafana
    GRAFANA_PASSWORD: Optional[str] = os.getenv("GRAFANA_PASSWORD")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Collector settings
    COLLECTOR_BATCH_SIZE: int = int(os.getenv("COLLECTOR_BATCH_SIZE", 100))
    COLLECTOR_RATE_LIMIT: int = int(os.getenv("COLLECTOR_RATE_LIMIT", 1))

    # Analyzer settings
    ANALYSIS_WORKERS: int = int(os.getenv("ANALYSIS_WORKERS", 4))
    SEMANTIC_MODEL: str = os.getenv("SEMANTIC_MODEL", "all-MiniLM-L6-v2")


settings = Settings()

if __name__ == "__main__":
    # Print out the settings to verify
    print(f"Running in {settings.ENVIRONMENT} mode.")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    if settings.TELEGRAM_API_ID:
        print("Telegram API ID is set.")
    else:
        print("Warning: Telegram API ID is not set.")
