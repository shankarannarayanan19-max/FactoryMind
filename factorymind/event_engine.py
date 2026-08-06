from typing import Dict, Any, List, Optional

# Verbatim §12 Event Taxonomy
VALID_EVENT_TYPES = {
    "ROOM_ENTERED",
    "ASSET_DISCOVERED",
    "STATE_CHANGED",
    "ALARM_OBSERVED",
    "SAFETY_HAZARD_OBSERVED",
    "MEASUREMENT_RECORDED",
    "SENSOR_CONTRADICTION",
    "ANOMALY_CONFIRMED",
    "SHUTDOWN_REQUESTED",
    "INSPECTION_HOLD_PLACED",
    "MISSION_COMPLETED",
    # System & Reconciliation events
    "LOCATION_TRANSITION_CONFLICT",
    "UNRESOLVED_ENTITY",
    "THRESHOLD_BREACH",
    "ASSET_HEALTH_DEGRADED",
    "WORLD_MODEL_UPDATED",
}

class EventEngine:
    """Event Engine for FactoryMind event taxonomy, logging, and emission (§12)."""

    def __init__(self):
        self.event_log: List[Dict[str, Any]] = []
        self._sequence = 0

    def emit(self, event_type: str, payload: Dict[str, Any], severity: str = "INFO", turn: int = 0) -> Dict[str, Any]:
        """Emit a structured domain event following §12 taxonomy."""
        self._sequence += 1
        event_id = f"EVT-{self._sequence:05d}"
        
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "severity": severity,
            "turn": turn,
            "payload": payload
        }
        self.event_log.append(event)
        return event

    def get_events(self, event_type: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter logged events by event_type or severity."""
        results = self.event_log
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        if severity:
            results = [e for e in results if e["severity"] == severity]
        return results

    def clear(self):
        self.event_log.clear()
        self._sequence = 0


