"""
models/transcription.py
------------------------
This module represents the "Transcription" entity and contains all
the database operations (Create, Read, Delete) related to it.

Keeping these functions separate from the Flask routes keeps the
routes thin and the data-access logic easy to find and test.
"""

from database.database import get_connection


def create_transcription(db_path, original_filename, language,
                          detected_language, transcription):
    """
    Insert a new transcription record into the database and return
    the full row (including its new auto-generated id) as a dict.
    """
    word_count = len(transcription.split())
    character_count = len(transcription)

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO transcriptions
            (original_filename, language, detected_language,
             transcription, word_count, character_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (original_filename, language, detected_language,
         transcription, word_count, character_count),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return get_transcription_by_id(db_path, new_id)


def get_all_transcriptions(db_path):
    """Return every saved transcription, newest first, as a list of dicts."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transcriptions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_transcription_by_id(db_path, transcription_id):
    """Return a single transcription by its id, or None if not found."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transcriptions WHERE id = ?", (transcription_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_transcription(db_path, transcription_id):
    """Delete a transcription by id. Returns True if a row was removed."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transcriptions WHERE id = ?", (transcription_id,)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
