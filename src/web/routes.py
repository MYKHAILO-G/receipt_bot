from flask import Blueprint, jsonify
web = Blueprint("web", __name__)

@web.route("/")
def home():
    return "OK"


@web.route("/health")
def health():
    return jsonify({
        "schemaVersion": 1,
        "label": "bot",
        "message": "online",
        "color": "brightgreen"
    })
