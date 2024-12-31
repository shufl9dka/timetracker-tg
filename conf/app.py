import os


class Config:
    MAX_RECENT_LABELS = 4

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SQL_ENGINE_URI = os.getenv("SQL_ENGINE_URI")
    REDIS_URI = os.getenv("REDIS_URI")

    FERNET_KEY = os.getenv("FERNET_KEY")
