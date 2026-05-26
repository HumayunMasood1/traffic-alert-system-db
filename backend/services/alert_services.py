import sys
sys.path.append('..')
from event_bus import IEventSubscriber

# ── DB integration (Idempotent Receiver persistence) ─────────
from db_manager import is_event_processed, mark_event_processed, save_log
# ─────────────────────────────────────────────────────────────


class AlertService(IEventSubscriber):
    def __init__(self):
        self.seen_ids = set()           # in-memory guard (unchanged)
        self.penalties_sent = 0
        self.blocked_duplicates = 0

    def handle(self, envelope):
        # ── IDEMPOTENCY CHECK (in-memory + DB) ────────────────
        # Primary: fast in-memory check (original logic, unchanged)
        if envelope.event_id in self.seen_ids:
            print(f"[AlertService] DUPLICATE BLOCKED: {envelope.event_id}")
            self.blocked_duplicates += 1
            return

        # Secondary: DB persistence check (survives restarts)
        if is_event_processed(envelope.event_id):
            print(f"[AlertService] DUPLICATE BLOCKED (DB): {envelope.event_id}")
            self.seen_ids.add(envelope.event_id)   # sync in-memory set
            self.blocked_duplicates += 1
            return
        # ─────────────────────────────────────────────────────

        self.seen_ids.add(envelope.event_id)

        # ── DB: persist this event as processed ───────────────
        mark_event_processed(envelope.event_id)
        # ─────────────────────────────────────────────────────

        payload = envelope.payload
        event_type = envelope.event_type

        if event_type == "SpeedViolationEvent":
            msg = f"Speed penalty issued to: {payload.get('vehicle_plate')} | {payload.get('speed')} km/h"
            print(f"[AlertService] {msg}")
            self.penalties_sent += 1
            # ── DB: save log entry ────────────────────────────
            save_log(event_type, msg)
            # ─────────────────────────────────────────────────

        elif event_type == "WrongWayDriverEvent":
            msg = f"Wrong-way penalty issued to: {payload.get('vehicle_plate')} | {payload.get('direction')}"
            print(f"[AlertService] {msg}")
            self.penalties_sent += 1
            # ── DB: save log entry ────────────────────────────
            save_log(event_type, msg)
            # ─────────────────────────────────────────────────
