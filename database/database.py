"""
database/database.py
---------------------
Small helper module that wraps SQLite so the rest of the app never
has to write raw SQL connection boilerplate.

We use SQLite because it needs zero setup - it is just a single file
on disk, which is perfect for a beginner-friendly local project.
"""

import sqlite3
import os


def get_connection(db_path):
    """
    Open a new SQLite connection to the given database file.

    `row_factory = sqlite3.Row` lets us access columns by name
    (e.g. row["transcription"]) instead of only by numeric index,
    which makes the rest of the code much easier to read.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    """
    Create the `transcriptions` table if it does not already exist.

    This is safe to call every time the app starts - `CREATE TABLE
    IF NOT EXISTS` will not wipe out existing data.
    """
    # Make sure the folder that will hold the .db file actually exists.
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            language TEXT NOT NULL,
            detected_language TEXT,
            transcription TEXT NOT NULL,
            word_count INTEGER NOT NULL,
            character_count INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.commit()
    conn.close()
