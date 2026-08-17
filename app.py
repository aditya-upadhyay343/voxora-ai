"""
app.py
------
Entry point for the AI Speech-to-Text Converter application.

Run this file to start the Flask development server:

    python app.py

Then open http://127.0.0.1:5000 in your web browser.
"""

import os
from flask import Flask

from config import Config
from database.database import init_db
from routes.transcription_routes import transcription_bp


def create_app():
    """Application factory: builds and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the folders the app depends on actually exist before
    # any request comes in (they may be missing on a fresh clone if
    # only the .gitkeep placeholder files were committed).
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)

    # Create the SQLite table(s) if they don't already exist.
    init_db(app.config["DATABASE_PATH"])

    # Register all the URL routes defined in routes/transcription_routes.py
    app.register_blueprint(transcription_bp)

    return app


app = create_app()


if __name__ == "__main__":
    # debug=True auto-reloads the server when you edit code, and shows
    # detailed error pages - very helpful while learning/building.
    app.run(debug=app.config["DEBUG"], host="127.0.0.1", port=5000)
