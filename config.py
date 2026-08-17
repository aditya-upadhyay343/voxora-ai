"""
config.py
---------
Central configuration for the AI Speech-to-Text application.

Keeping configuration in one place makes it easy to change settings
(like the upload folder or the maximum file size) without hunting
through the rest of the codebase.
"""

import os

# Absolute path to the project root (the folder this file lives in).
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base Flask configuration."""

    # Secret key is used by Flask to sign session cookies.
    # For a real production app you should set this via an environment
    # variable instead of hard-coding it.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Folder where uploaded audio files are temporarily stored before
    # they are transcribed and then deleted.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Folder where generated .txt transcription files are written to
    # so they can be downloaded by the user.
    OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

    # Path to the SQLite database file used to store transcription history.
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "transcriptions.db")

    # Maximum allowed upload size in bytes (25 MB). Flask will reject
    # anything larger than this with a 413 error automatically.
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB

    # Audio file extensions that the app is willing to accept.
    ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "flac", "ogg", "webm"}

    # Whisper model size. Smaller = faster but less accurate.
    # Options (smallest to largest): tiny, base, small, medium, large
    # "base" is a good balance of speed and accuracy for a beginner
    # laptop/desktop without a GPU.
    WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")

    # Languages the dropdown in the UI supports, mapped to the
    # language codes Whisper expects. "auto" means "let Whisper
    # detect the spoken language automatically".
    SUPPORTED_LANGUAGES = {
        "auto": "Auto Detect",
        "en": "English",
        "hi": "Hindi",
    }

    # Flask debug mode. Turn this off (False) if you ever deploy
    # this application publicly.
    DEBUG = True
