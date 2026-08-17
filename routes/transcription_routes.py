"""
routes/transcription_routes.py
--------------------------------
All the HTTP endpoints (URLs) related to transcription live here:
uploading/recording audio, running the AI model on it, listing
history, downloading a .txt file, and deleting history entries.

Keeping routes in a Blueprint (instead of directly in app.py) keeps
the project organized and makes it easy to add more route files
later (e.g. auth_routes.py) without app.py becoming huge.
"""

import os
import uuid

from flask import (
    Blueprint, request, jsonify, current_app, send_file, render_template
)
from werkzeug.utils import secure_filename

from services.speech_to_text import transcribe_audio, TranscriptionError
from models.transcription import (
    create_transcription, get_all_transcriptions,
    get_transcription_by_id, delete_transcription,
)

transcription_bp = Blueprint("transcription", __name__)


def _allowed_file(filename):
    """Check the file extension against the whitelist in config.py."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


# ---------------------------------------------------------------------
# Page routes (return HTML)
# ---------------------------------------------------------------------

@transcription_bp.route("/")
def index():
    """Main dashboard page: record/upload audio and see the result."""
    return render_template(
        "index.html", languages=current_app.config["SUPPORTED_LANGUAGES"]
    )


@transcription_bp.route("/history")
def history_page():
    """Page that lists every transcription made during this session."""
    return render_template("history.html")


# ---------------------------------------------------------------------
# API routes (return JSON)
# ---------------------------------------------------------------------

@transcription_bp.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """
    Accept an uploaded (or recorded) audio file, run it through the
    Whisper AI model, save the result to the database, and return the
    transcription as JSON.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file was included in the request."}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"error": "No file was selected."}), 400

    if not _allowed_file(audio_file.filename):
        allowed = ", ".join(sorted(current_app.config["ALLOWED_EXTENSIONS"]))
        return jsonify({
            "error": f"Unsupported file type. Allowed formats: {allowed}."
        }), 400

    language = request.form.get("language", "auto")
    if language not in current_app.config["SUPPORTED_LANGUAGES"]:
        language = "auto"

    # Build a safe, unique filename so two users uploading "audio.wav"
    # at the same time never overwrite each other's file.
    original_filename = secure_filename(audio_file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)

    audio_file.save(upload_path)

    try:
        # Double check the file actually has content and isn't empty/corrupt.
        if os.path.getsize(upload_path) == 0:
            raise TranscriptionError("The uploaded audio file is empty.")

        result = transcribe_audio(
            upload_path,
            model_size=current_app.config["WHISPER_MODEL_SIZE"],
            language=language,
        )

        record = create_transcription(
            current_app.config["DATABASE_PATH"],
            original_filename=original_filename,
            language=language,
            detected_language=result["detected_language"],
            transcription=result["text"],
        )

        return jsonify({"success": True, "transcription": record}), 200

    except TranscriptionError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:  # noqa: BLE001 - final safety net
        return jsonify({
            "error": f"An unexpected error occurred while transcribing: {exc}"
        }), 500
    finally:
        # Always clean up the temporary uploaded file, whether the
        # transcription succeeded or failed, so uploads/ never fills up.
        if os.path.exists(upload_path):
            os.remove(upload_path)


@transcription_bp.route("/api/history", methods=["GET"])
def api_history():
    """Return every stored transcription as JSON, newest first."""
    records = get_all_transcriptions(current_app.config["DATABASE_PATH"])
    return jsonify({"history": records}), 200


@transcription_bp.route("/api/history/<int:transcription_id>", methods=["DELETE"])
def api_delete_history(transcription_id):
    """Delete a single transcription record from history."""
    deleted = delete_transcription(
        current_app.config["DATABASE_PATH"], transcription_id
    )
    if not deleted:
        return jsonify({"error": "Transcription not found."}), 404
    return jsonify({"success": True}), 200


@transcription_bp.route("/api/download/<int:transcription_id>", methods=["GET"])
def api_download(transcription_id):
    """
    Generate a .txt file for a given transcription on the fly and send
    it to the browser as a download.
    """
    record = get_transcription_by_id(
        current_app.config["DATABASE_PATH"], transcription_id
    )
    if not record:
        return jsonify({"error": "Transcription not found."}), 404

    # Write the text out to the outputs/ folder using a safe filename.
    txt_filename = f"transcription_{transcription_id}.txt"
    txt_path = os.path.join(current_app.config["OUTPUT_FOLDER"], txt_filename)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(record["transcription"])

    return send_file(
        txt_path,
        mimetype="text/plain",
        as_attachment=True,
        download_name=txt_filename,
    )
