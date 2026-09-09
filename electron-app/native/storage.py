import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import app_data_dir


class Storage:
    def __init__(self, path: Path | None = None):
        self.path = path or app_data_dir() / "altwisp.db"
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self):
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    final_text TEXT NOT NULL,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    app_name TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS dictionary (
                    id INTEGER PRIMARY KEY,
                    spoken TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    replacement TEXT NOT NULL,
                    starred INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY,
                    trigger TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    expansion TEXT NOT NULL
                );
                """
            )

    def add_history(self, raw_text, final_text, duration_seconds=0, app_name=""):
        with self._connect() as db:
            db.execute(
                "INSERT INTO history(created_at, raw_text, final_text, duration_seconds, app_name) VALUES (?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), raw_text, final_text, duration_seconds, app_name),
            )

    def recent_history(self, limit=100):
        with self._connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))]

    def stats(self):
        with self._connect() as db:
            row = db.execute(
                "SELECT COUNT(*) AS dictations, COALESCE(SUM(duration_seconds), 0) AS seconds, "
                "COALESCE(SUM(LENGTH(TRIM(final_text)) - LENGTH(REPLACE(TRIM(final_text), ' ', '')) + 1), 0) AS words "
                "FROM history WHERE final_text <> ''"
            ).fetchone()
            return dict(row)

    def delete_history(self):
        with self._connect() as db:
            db.execute("DELETE FROM history")

    def prune_history(self, older_than_hours):
        if older_than_hours <= 0:
            return
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=older_than_hours)).isoformat()
        with self._connect() as db:
            db.execute("DELETE FROM history WHERE created_at < ?", (cutoff,))

    def list_entries(self, table):
        if table not in {"dictionary", "snippets"}:
            raise ValueError("Unsupported table")
        with self._connect() as db:
            return [dict(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY id DESC")]

    def upsert_dictionary(self, spoken, replacement):
        with self._connect() as db:
            db.execute(
                "INSERT INTO dictionary(spoken, replacement) VALUES (?, ?) "
                "ON CONFLICT(spoken) DO UPDATE SET replacement=excluded.replacement",
                (spoken.strip(), replacement.strip()),
            )

    def upsert_snippet(self, trigger, expansion):
        with self._connect() as db:
            db.execute(
                "INSERT INTO snippets(trigger, expansion) VALUES (?, ?) "
                "ON CONFLICT(trigger) DO UPDATE SET expansion=excluded.expansion",
                (trigger.strip(), expansion),
            )

    def delete_entry(self, table, entry_id):
        if table not in {"dictionary", "snippets"}:
            raise ValueError("Unsupported table")
        with self._connect() as db:
            db.execute(f"DELETE FROM {table} WHERE id = ?", (entry_id,))

    def export_json(self, destination):
        payload = {
            "history": self.recent_history(100000),
            "dictionary": self.list_entries("dictionary"),
            "snippets": self.list_entries("snippets"),
        }
        Path(destination).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
