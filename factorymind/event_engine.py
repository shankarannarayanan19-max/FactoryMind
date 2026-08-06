"""Event Engine for FactoryMind event taxonomy and emission."""

class EventEngine:
    def __init__(self):
        self.event_log = []

    def emit(self, event_type: str, payload: dict):
        event = {"event_type": event_type, "payload": payload}
        self.event_log.append(event)
        return event
