import uuid
from datetime import datetime

class EventEnvelope:
    def __init__(self, payload, source_id, event_type):
        self.event_id = str(uuid.uuid4())
        self.correlation_id = str(uuid.uuid4())
        self.schema_version = 1
        self.source_id = source_id
        self.timestamp = datetime.utcnow().isoformat()
        self.event_type = event_type
        self.payload = payload

class VehicleDetectedEvent:
    def __init__(self, camera_id, vehicle_plate, lane_number="unknown"):
        self.camera_id = camera_id
        self.vehicle_plate = vehicle_plate
        self.lane_number = lane_number

class SpeedViolationEvent:
    def __init__(self, camera_id, vehicle_plate, speed, speed_limit):
        self.camera_id = camera_id
        self.vehicle_plate = vehicle_plate
        self.speed = speed
        self.speed_limit = speed_limit

class CongestionAlertEvent:
    def __init__(self, camera_id, vehicle_count, intersection):
        self.camera_id = camera_id
        self.vehicle_count = vehicle_count
        self.intersection = intersection

class TrafficClearedEvent:
    def __init__(self, camera_id, intersection):
        self.camera_id = camera_id
        self.intersection = intersection

class WrongWayDriverEvent:
    def __init__(self, camera_id, vehicle_plate, direction):
        self.camera_id = camera_id
        self.vehicle_plate = vehicle_plate
        self.direction = direction