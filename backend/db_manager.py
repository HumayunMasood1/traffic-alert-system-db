"""
DBManager — SQLite helper for Traffic Alert System
----------------------------------------------------
Provides three simple persistence layers:
  1. outbox_events   — Outbox Pattern: events saved before publishing
  2. processed_events — Idempotent Receiver: persistent duplicate guard
  3. logs            — LoggingService: persisted alert/violation records

All methods fail silently if the DB is unavailable, so the system
continues to run in in-memory mode without crashing.
"""

import sqlite3
import os
from datetime import datetime

# Database file lives in the backend folder alongside app.py
DB_PATH = os.path.join(os.path.dirname(__file__), "traffic_alerts.db")


def _get_connection():
    """
    Open and return a SQLite connection.
    Raises sqlite3.Error on failure — callers catch this.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets you access columns by name
    return conn


def init_db():
    """
    Create all three tables if they do not already exist.
    Called once at startup from app.py.
    Returns True if DB initialized successfully, False otherwise.
    """
    create_outbox = """
        CREATE TABLE IF NOT EXISTS outbox_events (
            event_id       TEXT PRIMARY KEY,
            correlation_id TEXT,
            event_type     TEXT NOT NULL,
            payload        TEXT,
            timestamp      DATETIME NOT NULL,
            status         TEXT NOT NULL DEFAULT 'PENDING'
        );
    """
    create_processed = """
        CREATE TABLE IF NOT EXISTS processed_events (
            event_id       TEXT PRIMARY KEY,
            processed_time DATETIME NOT NULL
        );
    """
    create_logs = """
        CREATE TABLE IF NOT EXISTS logs (
            log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            message    TEXT,
            timestamp  DATETIME NOT NULL
        );
    """
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(create_outbox)
        cur.execute(create_processed)
        cur.execute(create_logs)
        conn.commit()
        conn.close()
        print("[DBManager] Database initialized successfully.")
        return True
    except sqlite3.Error as e:
        print(f"[DBManager] WARNING: Could not initialize DB — {e}")
        print("[DBManager] System will continue in in-memory-only mode.")
        return False


# ──────────────────────────────────────────────
# OUTBOX PATTERN
# ──────────────────────────────────────────────

def insert_outbox_event(event_id, correlation_id, event_type, payload, timestamp):
    """
    Save an event to outbox_events with status='PENDING'
    before it is published to the EventBus.

    Parameters
    ----------
    event_id       : str  — UUID from EventEnvelope.event_id
    correlation_id : str  — UUID from EventEnvelope.correlation_id
    event_type     : str  — e.g. 'SpeedViolationEvent'
    payload        : str  — JSON-serialised payload string
    timestamp      : str  — ISO datetime string from EventEnvelope.timestamp
    """
    sql = """
        INSERT OR IGNORE INTO outbox_events
            (event_id, correlation_id, event_type, payload, timestamp, status)
        VALUES (?, ?, ?, ?, ?, 'PENDING');
    """
    try:
        conn = _get_connection()
        conn.execute(sql, (event_id, correlation_id, event_type, payload, timestamp))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[DBManager] insert_outbox_event failed: {e}")


def mark_event_sent(event_id):
    """
    Update outbox_events status to 'SENT' after the EventBus
    has successfully dispatched the event to all subscribers.

    Parameters
    ----------
    event_id : str — the UUID of the event to mark
    """
    sql = "UPDATE outbox_events SET status = 'SENT' WHERE event_id = ?;"
    try:
        conn = _get_connection()
        conn.execute(sql, (event_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[DBManager] mark_event_sent failed: {e}")


# ──────────────────────────────────────────────
# IDEMPOTENT RECEIVER PERSISTENCE
# ──────────────────────────────────────────────

def is_event_processed(event_id):
    """
    Check if an event_id already exists in processed_events.
    Returns True if it was previously processed, False otherwise.
    Falls back to False (allowing processing) if DB is unavailable.

    Parameters
    ----------
    event_id : str — the UUID to check
    """
    sql = "SELECT 1 FROM processed_events WHERE event_id = ? LIMIT 1;"
    try:
        conn = _get_connection()
        row = conn.execute(sql, (event_id,)).fetchone()
        conn.close()
        return row is not None
    except sqlite3.Error as e:
        print(f"[DBManager] is_event_processed failed: {e}")
        return False   # fail open: let in-memory check handle it


def mark_event_processed(event_id):
    """
    Insert an event_id into processed_events after it has been
    handled by a subscriber for the first time.

    Parameters
    ----------
    event_id : str — the UUID to record
    """
    sql = """
        INSERT OR IGNORE INTO processed_events (event_id, processed_time)
        VALUES (?, ?);
    """
    try:
        conn = _get_connection()
        conn.execute(sql, (event_id, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[DBManager] mark_event_processed failed: {e}")


# ──────────────────────────────────────────────
# LOGGING PERSISTENCE
# ──────────────────────────────────────────────

def save_log(event_type, message):
    """
    Persist a log entry (alert, violation, congestion, etc.)
    into the logs table.

    Parameters
    ----------
    event_type : str — e.g. 'SpeedViolationEvent'
    message    : str — human-readable description of what happened
    """
    sql = """
        INSERT INTO logs (event_type, message, timestamp)
        VALUES (?, ?, ?);
    """
    try:
        conn = _get_connection()
        conn.execute(sql, (event_type, message, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[DBManager] save_log failed: {e}")
