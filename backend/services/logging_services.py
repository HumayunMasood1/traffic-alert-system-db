import sys
sys.path.append('..')
from event_bus import IEventSubscriber

# ── DB integration (log persistence) ─────────────────────────
from db_manager import save_log
# ─────────────────────────────────────────────────────────────


class LoggingService(IEventSubscriber):
    def __init__(self):
        self.seen_ids = set()           # in-memory guard (unchanged)
        self.logs = []                  # in-memory log list (unchanged)

    def handle(self, envelope):
        # IDEMPOTENCY CHECK — original logic unchanged
        if envelope.event_id in self.seen_ids:
            print(f"[LoggingService] DUPLICATE BLOCKED: {envelope.event_id}")
            return

        self.seen_ids.add(envelope.event_id)

        log_entry = {
            "event_id": envelope.event_id,
            "event_type": envelope.event_type,
            "source": envelope.source_id,
            "time": envelope.timestamp,
            "payload": envelope.payload
        }
        self.logs.append(log_entry)         # in-memory append (unchanged)
        print(f"[LoggingService] Logged: {envelope.event_type} from {envelope.source_id}")

        # ── DB: persist the log entry ─────────────────────────
        message = f"source={envelope.source_id} | payload={envelope.payload}"
        save_log(envelope.event_type, message)
        # ─────────────────────────────────────────────────────
