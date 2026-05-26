from flask import Flask, jsonify, request
from flask_cors import CORS

from event_bus import EventBus
from models import EventEnvelope

from services.alert_services import AlertService
from services.logging_services import LoggingService
from services.dashboard_service import DashboardService
from services.wrongway_service import WrongWayService

# ── DB integration (Outbox Pattern) ──────────────────────────
import json
from db_manager import init_db, insert_outbox_event, mark_event_sent
# ─────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

# ====================================
# CREATE EVENT BUS
# ====================================
bus = EventBus()

# ====================================
# CREATE SERVICES
# ====================================
alert = AlertService()
logger = LoggingService()
dashboard = DashboardService()
wrongway = WrongWayService()

# ====================================
# SUBSCRIBE SERVICES TO EVENTS
# ====================================
bus.subscribe("SpeedViolationEvent", alert)
bus.subscribe("SpeedViolationEvent", logger)

bus.subscribe("VehicleDetectedEvent", dashboard)
bus.subscribe("VehicleDetectedEvent", logger)

bus.subscribe("CongestionAlertEvent", dashboard)
bus.subscribe("CongestionAlertEvent", logger)

bus.subscribe("TrafficClearedEvent", dashboard)

bus.subscribe("WrongWayDriverEvent", alert)
bus.subscribe("WrongWayDriverEvent", wrongway)
bus.subscribe("WrongWayDriverEvent", logger)

# ====================================
# STORE EVENTS FOR DUPLICATE TESTING
# ====================================
event_store = {}

# ── DB: initialize tables at startup ─────────────────────────
init_db()   # safe no-op if DB unavailable; system runs in-memory
# ─────────────────────────────────────────────────────────────


# ====================================
# PUBLISH EVENT
# ====================================
@app.route('/api/publish', methods=['POST'])
def publish_event():

    data = request.json

    envelope = EventEnvelope(
        payload=data['payload'],
        source_id=data['source_id'],
        event_type=data['event_type']
    )

    # Save event for duplicate testing
    event_store[envelope.event_id] = envelope

    # ── DB: Outbox Pattern — save BEFORE publishing ───────────
    insert_outbox_event(
        event_id=envelope.event_id,
        correlation_id=envelope.correlation_id,
        event_type=envelope.event_type,
        payload=json.dumps(envelope.payload),
        timestamp=envelope.timestamp
    )
    # ─────────────────────────────────────────────────────────

    # Publish event (EventBus + Observer logic UNCHANGED)
    bus.publish(envelope)

    # ── DB: Outbox Pattern — mark SENT after dispatch ─────────
    mark_event_sent(envelope.event_id)
    # ─────────────────────────────────────────────────────────

    return jsonify({
        "status": "published",
        "event_id": envelope.event_id,
        "penalties_sent": alert.penalties_sent,
        "duplicates_blocked": alert.blocked_duplicates,
        "queue_size": bus.get_queue_size()
    })


# ====================================
# DUPLICATE EVENT TEST
# ====================================
@app.route('/api/publish_duplicate', methods=['POST'])
def publish_duplicate():

    data = request.json
    event_id = data['event_id']

    if event_id not in event_store:
        return jsonify({
            "error": "Original event not found"
        }), 404

    duplicate_event = event_store[event_id]
    bus.publish(duplicate_event)

    return jsonify({
        "status": "duplicate_sent",
        "event_id": duplicate_event.event_id,
        "penalties_sent": alert.penalties_sent,
        "duplicates_blocked": alert.blocked_duplicates,
        "queue_size": bus.get_queue_size()
    })


# ====================================
# SYSTEM STATUS
# ====================================
@app.route('/api/status', methods=['GET'])
def get_status():

    return jsonify({
        "running": True,
        "penalties": alert.penalties_sent,
        "penalties_sent": alert.penalties_sent,
        "duplicates_blocked": alert.blocked_duplicates,
        "total_logs": len(logger.logs),
        "active_congestions": dashboard.active_congestions,
        "queue_size": bus.get_queue_size(),
        "wrongway_alerts": wrongway.alerts_sent
    })


# ====================================
# GET LOGS
# ====================================
@app.route('/api/logs', methods=['GET'])
def get_logs():

    return jsonify({
        "logs": logger.logs
    })


# ====================================
# START SERVER
# ====================================
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
