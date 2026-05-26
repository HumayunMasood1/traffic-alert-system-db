import sys
sys.path.append('..')
from event_bus import IEventSubscriber

class WrongWayService(IEventSubscriber):
    def __init__(self):
        self.seen_ids = set()
        self.alerts_sent = 0

    def handle(self, envelope):
        if envelope.event_id in self.seen_ids:
            print(f"[WrongWayService] DUPLICATE BLOCKED: {envelope.event_id}")
            return

        self.seen_ids.add(envelope.event_id)
        p = envelope.payload
        print(f"[WrongWayService] WRONG WAY ALERT: {p.get('vehicle_plate')} going {p.get('direction')}")
        self.alerts_sent += 1