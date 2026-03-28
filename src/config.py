import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    FILE_NAME = "../data/bot_config/keys.json"
    
    if not os.path.exists(FILE_NAME):
        raise FileNotFoundError("Config file not found")

    with open(FILE_NAME, "r") as f:
        config = json.load(f)

    BOT_TOKEN = config.get("bot_token")
    GEMINI_API_KEY = config.get("gemini_api_key")