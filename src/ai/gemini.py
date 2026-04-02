
from google import genai
import json
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def clean_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]

    return text


def parse_receipt(image_bytes):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": "Extract receipt data and return ONLY JSON with date, store, items, without any explanations. The JSON should be in the format: {date: '', store: '', items: [{name: '', price: ''}, ...]}, and the date should be in the format YYYY-MM-DD., and the price should be a number without currency symbols. If any of these fields cannot be extracted, return an empty string for that field. Dont use markdown, only return raw JSON."},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_bytes
                        }
                    }
                ]
            }
        ]
    )

    raw = response.text
    clean = clean_json(raw)
    data = json.loads(clean)
    return data

# from google import genai
# from config import GEMINI_API_KEY

# client = genai.Client(api_key=GEMINI_API_KEY)

# def parse_receipt(image_bytes):
#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=[
#             {
#                 "role": "user",
#                 "parts": [
#                     {"text": "Extract receipt data and return ONLY JSON with date, store, total, items"},
#                     {
#                         "inline_data": {
#                             "mime_type": "image/jpeg",
#                             "data": image_bytes
#                         }
#                     }
#                 ]
#             }
#         ]
#     )

#     return response.text