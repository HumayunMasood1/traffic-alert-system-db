-- ============================================================
-- Traffic Alert System — SQLite Schema
-- ============================================================
-- Run this file manually to create the tables, or let
-- DBManager.init_db() create them automatically at startup.
-- ============================================================

-- 1. OUTBOX PATTERN TABLE
--    Every event is saved here BEFORE being published to the
--    EventBus, then status is updated to SENT after dispatch.
CREATE TABLE IF NOT EXISTS outbox_events (
    event_id       TEXT PRIMARY KEY,       -- UUID from EventEnvelope
    correlation_id TEXT,                   -- UUID for tracing related events
    event_type     TEXT NOT NULL,          -- e.g. SpeedViolationEvent
    payload        TEXT,                   -- JSON string of the event payload
    timestamp      DATETIME NOT NULL,      -- UTC time the event was created
    status         TEXT NOT NULL           -- PENDING or SENT
                   DEFAULT 'PENDING'
);

-- 2. IDEMPOTENT RECEIVER TABLE
--    Persists processed event IDs so the duplicate check survives
--    a server restart (complements the in-memory seen_ids set).
CREATE TABLE IF NOT EXISTS processed_events (
    event_id       TEXT PRIMARY KEY,       -- UUID of the processed event
    processed_time DATETIME NOT NULL       -- UTC time it was first handled
);

-- 3. LOG PERSISTENCE TABLE
--    All alerts, violations, and congestion events are saved here
--    by LoggingService for audit and reporting purposes.
CREATE TABLE IF NOT EXISTS logs (
    log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,              -- e.g. SpeedViolationEvent
    message    TEXT,                       -- human-readable summary
    timestamp  DATETIME NOT NULL           -- UTC time logged
);
