import sys
sys.path.append('..')
from event_bus import IEventSubscriber

class DashboardService(IEventSubscriber):
    def __init__(self):
        self.seen_ids = set()
        self.active_congestions = []

    def handle(self, envelope):
        if envelope.event_id in self.seen_ids:
            return

        self.seen_ids.add(envelope.event_id)
        event_type = envelope.event_type
        payload = envelope.payload

        if event_type == "CongestionAlertEvent":
            self.active_congestions.append(payload.get("intersection"))
            print(f"[Dashboard] Congestion at: {payload.get('intersection')}")

        elif event_type == "TrafficClearedEvent":
            intersection = payload.get("intersection")
            if intersection in self.active_congestions:
                self.active_congestions.remove(intersection)
            print(f"[Dashboard] Cleared: {intersection}")

        elif event_type == "VehicleDetectedEvent":
            print(f"[Dashboard] Vehicle spotted: {payload.get('vehicle_plate')}")