import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
POSTGRES_HREF = os.getenv("POSTGRES_HREF")

if not BOT_TOKEN or not GEMINI_API_KEY or not POSTGRES_HREF:
    FILE_NAME = os.path.join(os.path.dirname(__file__), "../data/bot_config/keys.json")
    
    if not os.path.exists(FILE_NAME):
        raise FileNotFoundError(f"Config file {FILE_NAME} not found")

    with open(FILE_NAME, "r") as f:
        config = json.load(f)

    BOT_TOKEN = config.get("bot_token")
    GEMINI_API_KEY = config.get("gemini_api_key")
    POSTGRES_HREF = config.get("postgres_href")