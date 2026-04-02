from flask import Flask

from web.routes import web

flask_app = Flask(__name__)
flask_app.register_blueprint(web)

def run_flask():
    """Run Flask in a background daemon thread so it doesn't block the bot."""
    flask_app.run(host="0.0.0.0", port=10000)
