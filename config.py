import os
import json

FILE_NAME = "data/bot_config/keys.json"
if not os.path.exists(FILE_NAME):
    raise FileNotFoundError("Config file not found")

with open(FILE_NAME, "r") as f:
    config = json.load(f)

BOT_TOKEN = config.get("bot_token")
GEMINI_API_KEY = config.get("gemini_api_key")