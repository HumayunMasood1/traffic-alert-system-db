# Traffic Alert System — Event-Driven CEP with SQLite

A real-time traffic alert system built using Complex Event Processing (CEP) 
principles in Python. Features an event-driven architecture with Observer Pattern, 
EventBus, EventEnvelope, and Idempotent Receiver Pattern — enhanced with a 
lightweight SQLite database layer.

## Architecture

- **EventBus** — Central message broker for publishing and subscribing to events
- **Observer Pattern** — Services (AlertService, LoggingService, etc.) subscribe to events
- **EventEnvelope** — Wraps every event with ID, timestamp, correlation ID, and payload
- **Idempotent Receiver** — Prevents duplicate event processing (in-memory + DB)
- **Outbox Pattern** — Events saved to DB before publishing, marked SENT after dispatch

## Database Layer (SQLite)

Three tables managed by `DBManager`:

| Table | Purpose |
|---|---|
| `outbox_events` | Stores events before publishing (PENDING → SENT) |
| `processed_events` | Persists processed event IDs for duplicate detection |
| `logs` | Stores all alerts, violations, and congestion events |

## Tech Stack

- Python 3.x
- Flask + Flask-CORS
- SQLite3 (built-in, no installation needed)
- HTML / CSS / JavaScript (frontend dashboard)

## How to Run

1. Install dependencies:
pip install flask flask-cors

2. Start the backend:
cd backend
python app.py

3. Open `frontend/index.html` in your browser

## Event Types

- `SpeedViolationEvent` — Triggered when a vehicle exceeds speed limit
- `WrongWayDriverEvent` — Triggered when wrong-way driving is detected
- `VehicleDetectedEvent` — Triggered on vehicle detection at a sensor
- `CongestionAlertEvent` — Triggered when traffic congestion is detected
- `TrafficClearedEvent` — Triggered when congestion clears

## Database Location

After running, the SQLite database is created at:
backend/traffic_alerts.db
Open with [DB Browser for SQLite](https://sqlitebrowser.org/) to inspect tables.
