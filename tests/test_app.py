"""
tests/test_app.py
------------------
Basic automated tests for the Flask application.

Run with:
    pytest

These tests do NOT load the actual Whisper AI model (that would be
slow and require downloading model weights), so they focus on
checking that the web server, routes, and validation logic behave
correctly. Anything that calls into services/speech_to_text.py is
skipped or checked only for correct error handling.
"""

import io
import os
import sys

# Make sure the project root is on the Python path so `import app` works
# no matter which folder pytest is run from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app


@pytest.fixture
def client():
    """Provide a Flask test client backed by a temporary test database."""
    app = create_app()
    app.config["TESTING"] = True

    # Use a separate test database so we never touch real history data.
    test_db_path = os.path.join(
        os.path.dirname(app.config["DATABASE_PATH"]), "test_transcriptions.db"
    )
    app.config["DATABASE_PATH"] = test_db_path

    from database.database import init_db
    init_db(test_db_path)

    with app.test_client() as test_client:
        yield test_client

    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def test_home_page_loads(client):
    """The home page ('/') should load successfully and mention the app title."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"AI Speech-to-Text Converter" in response.data


def test_history_page_loads(client):
    """The history page should load successfully."""
    response = client.get("/history")
    assert response.status_code == 200
    assert b"History" in response.data


def test_api_history_empty(client):
    """A fresh database should report an empty history list."""
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.get_json()
    assert data["history"] == []


def test_transcribe_with_no_file_returns_error(client):
    """Calling /api/transcribe with no audio file at all should fail cleanly."""
    response = client.post("/api/transcribe", data={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_transcribe_with_invalid_extension_returns_error(client):
    """Uploading a disallowed file type (e.g. .txt) should be rejected."""
    fake_file = (io.BytesIO(b"this is not audio"), "notes.txt")
    response = client.post(
        "/api/transcribe",
        data={"audio": fake_file, "language": "auto"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Unsupported file type" in data["error"]


def test_download_missing_transcription_returns_404(client):
    """Requesting a download for an id that doesn't exist should 404."""
    response = client.get("/api/download/99999")
    assert response.status_code == 404


def test_delete_missing_transcription_returns_404(client):
    """Deleting an id that doesn't exist should return 404, not crash."""
    response = client.delete("/api/history/99999")
    assert response.status_code == 404
