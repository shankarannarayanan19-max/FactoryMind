"""Persistent World Model for FactoryMind adhering strictly to §11 schema and §10 reconciliation rules."""

from typing import Dict, Any, List, Optional
from factorymind.config_loader import ConfigLoader

class WorldModel:
    """Persistent World Model for FactoryMind maintaining state-of-truth (§11)."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader

        self.factory: Dict[str, Any] = {"name": "Canonical Factory", "version": "1.0"}
        self.agent: Dict[str, Any] = {
            "location": "UNKNOWN",
            "confidence": 0.0,
            "source": "unknown",
            "last_observed_turn": 0
        }
        self.rooms: Dict[str, Any] = {}
        self.assets: Dict[str, Any] = {}
        self.sensors: Dict[str, Any] = {}
        self.relationships: List[Dict[str, Any]] = []
        self.latest_measurements: Dict[str, Any] = {}
        self.measurement_history: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []
        self.mission_state: Dict[str, Any] = {}
        self.action_history: List[Dict[str, Any]] = []
        self.reports: List[Dict[str, Any]] = []

        # Populate initial asset registry structures
        self._initialize_from_config()

    def _initialize_from_config(self):
        """Pre-populate assets and sensors from config registry using canonical IDs and aliases."""
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})

        for rid, rdata in rooms_cfg.items():
            self.rooms[rid] = {
                "name": rdata.get("name", rid),
                "description": rdata.get("description", ""),
                "exits": rdata.get("exits", {}),
                "last_observed_turn": 0
            }

        for aid, adata in assets_cfg.items():
            self.assets[aid] = {
                "asset_id": aid,
                "name": adata.get("name", aid),
                "type": adata.get("type", "ASSET"),
                "room": adata.get("room", "UNKNOWN"),
                "operational_state": "RUNNING" if "CV" in aid else "UNKNOWN",
                "energy_state": "ENERGIZED" if "CV" in aid else "UNKNOWN",
                "access_state": "CLOSED" if "GUARD" in aid else "NORMAL",
                "safety_state": "ENGAGED" if "GUARD" in aid else "NORMAL",
                "health_state": "NORMAL",
                "aliases": [adata.get("name", aid).lower(), aid.lower()] + [al.lower() for al in adata.get("aliases", [])],
                "state_history": [],

                "last_observed_turn": 0,
                "confidence": 1.0
            }
            # Initial static relationships (Rule 3)
            if "part_of" in adata:
                self.add_relationship_rule1_3(aid, "part_of", adata["part_of"], turn=0)
            if "protects" in adata:
                self.add_relationship_rule1_3(aid, "protects", adata["protects"], turn=0)
            if "controls" in adata:
                self.add_relationship_rule1_3(aid, "controls", adata["controls"], turn=0)
            if "room" in adata:
                self.add_relationship_rule1_3(aid, "located_in", adata["room"], turn=0)

        for sid, sdata in sensors_cfg.items():
            self.sensors[sid] = {
                "sensor_id": sid,
                "name": sdata.get("name", sid),
                "type": sdata.get("type", "SENSOR"),
                "sensor_type": sdata.get("sensor_type", "TELEMETRY"),
                "monitored_asset": sdata.get("monitors"),
                "unit": sdata.get("unit", ""),
                "latest_value": None,
                "status": "NORMAL",
                "last_observed_turn": 0,
                "confidence": 1.0
            }
            if "monitors" in sdata:
                self.add_relationship_rule1_3(sid, "monitors", sdata["monitors"], turn=0)

    def resolve_asset_id(self, alias_or_id: str) -> str:
        """Resolve any alias or name to canonical asset ID. Never creates a duplicate asset record (§2 Step 2)."""
        if not alias_or_id:
            return alias_or_id

        target = alias_or_id.strip()
        if target in self.assets:
            return target
        if target in self.sensors:
            return target

        target_lower = target.lower()
        for aid, adata in self.assets.items():
            aname = adata.get("name", "").lower()
            if target_lower == aid.lower() or target_lower == aname:
                return aid
            if target_lower in [a.lower() for a in adata.get("aliases", [])]:
                return aid
            # Partial substring alias match (e.g., "Tail Drive Motor" matching "Tail Drive Motor & Bearing Assembly")
            if target_lower in aname or (len(target_lower) > 4 and target_lower in aname):
                return aid

        for sid, sdata in self.sensors.items():
            sname = sdata.get("name", "").lower()
            if target_lower == sid.lower() or target_lower == sname:
                return sid
            if target_lower in sname or (len(target_lower) > 4 and target_lower in sname):
                return sid


        return target

    def update_agent_location(self, room_id: str, confidence: float = 1.0, source: str = "deterministic_parser", turn: int = 0):
        self.agent = {
            "location": room_id,
            "confidence": confidence,
            "source": source,
            "last_observed_turn": turn
        }

    def update_asset_state_rule2(self, asset_id: str, state_key: str, value: Any, turn: int = 0) -> Dict[str, Any]:
        """Reconciliation Rule 2: Newer dynamic state replaces old value in snapshot; old value moves to history.
        Emits degradation flag if health state degrades from NORMAL to WARNING/CRITICAL.
        """
        canonical_id = self.resolve_asset_id(asset_id)
        if canonical_id not in self.assets:
            self.assets[canonical_id] = {
                "asset_id": canonical_id,
                "health_state": "NORMAL",
                "state_history": [],
                "last_observed_turn": turn,
                "confidence": 1.0
            }

        asset = self.assets[canonical_id]
        old_val = asset.get(state_key)

        state_changed = False
        degraded = False

        if old_val != value:
            state_changed = True
            if old_val is not None:
                asset["state_history"].append({
                    "turn": turn,
                    "state_key": state_key,
                    "old_value": old_val,
                    "new_value": value
                })
            asset[state_key] = value

            # Detect degradation (e.g. NORMAL -> WARNING or NORMAL -> CRITICAL)
            if state_key == "health_state":
                if old_val == "NORMAL" and value in ("WARNING", "CRITICAL"):
                    degraded = True
                elif old_val == "WARNING" and value == "CRITICAL":
                    degraded = True

        # Rule 1: Refresh turn & boost confidence on observation
        asset["last_observed_turn"] = turn
        asset["confidence"] = min(1.0, asset.get("confidence", 0.8) + 0.05)

        return {
            "asset_id": canonical_id,
            "state_changed": state_changed,
            "degraded": degraded,
            "old_value": old_val,
            "new_value": value
        }


    def update_asset_state(self, asset_id: str, state_key: str, value: Any, turn: int = 0) -> bool:
        """Backwards compatible update helper wrapping Rule 2."""
        res = self.update_asset_state_rule2(asset_id, state_key, value, turn)
        return res["state_changed"]

    def add_relationship_rule1_3(self, source: str, relation: str, target: str, turn: int = 0, confidence: float = 1.0):
        """Reconciliation Rules 1 & 3: Preserves static relationships and updates turn/confidence on repetition."""
        src_id = self.resolve_asset_id(source)
        tgt_id = self.resolve_asset_id(target)

        for rel in self.relationships:
            if rel["source"] == src_id and rel["relation"] == relation and rel["target"] == tgt_id:
                # Rule 1: Refresh turn & confidence
                rel["last_observed_turn"] = turn
                rel["confidence"] = min(1.0, rel["confidence"] + 0.05)
                return rel

        new_rel = {
            "source": src_id,
            "relation": relation,
            "target": tgt_id,
            "confidence": confidence,
            "last_observed_turn": turn
        }
        self.relationships.append(new_rel)
        return new_rel

    def add_contradiction_rule4(
        self,
        fixed_sensor_id: str,
        portable_tool_id: str,
        fixed_val: float,
        portable_val: float,
        target_asset: str,
        turn: int
    ) -> Dict[str, Any]:
        """Reconciliation Rule 4: Handle contradicting measurements.
        Creates CONTRADICTS relationship, sets status SENSOR_VALIDATION_REQUIRED.
        NEVER averages readings.
        """
        fixed_id = self.resolve_asset_id(fixed_sensor_id)
        tool_id = self.resolve_asset_id(portable_tool_id)
        asset_id = self.resolve_asset_id(target_asset)

        # Create CONTRADICTS relationship
        rel = self.add_relationship_rule1_3(fixed_id, "CONTRADICTS", tool_id, turn=turn, confidence=1.0)
        rel["details"] = {
            "fixed_value": fixed_val,
            "portable_value": portable_val,
            "monitored_asset": asset_id
        }

        # Set status to SENSOR_VALIDATION_REQUIRED (never average!)
        if fixed_id in self.sensors:
            self.sensors[fixed_id]["status"] = "SENSOR_VALIDATION_REQUIRED"
            self.sensors[fixed_id]["contradicting_value"] = portable_val

        if tool_id in self.sensors:
            self.sensors[tool_id]["status"] = "SENSOR_VALIDATION_REQUIRED"

        # Update latest measurement for fixed sensor to mark validation required without overwriting original reading with average
        if fixed_id in self.latest_measurements:
            self.latest_measurements[fixed_id]["status"] = "SENSOR_VALIDATION_REQUIRED"

        return rel

    def update_sensor_reading(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        status: str = "NORMAL",
        monitored_asset: Optional[str] = None,
        alarm: Optional[str] = None,
        turn: int = 0
    ):
        sid = self.resolve_asset_id(sensor_id)
        asset_id = self.resolve_asset_id(monitored_asset) if monitored_asset else None

        measurement = {
            "sensor_id": sid,
            "monitored_asset": asset_id,
            "value": value,
            "unit": unit,
            "status": status,
            "alarm": alarm,
            "turn": turn
        }
        self.latest_measurements[sid] = measurement
        self.measurement_history.append(measurement)

        if sid not in self.sensors:
            self.sensors[sid] = {
                "sensor_id": sid,
                "name": sid,
                "type": "SENSOR",
                "unit": unit,
                "status": status
            }
        
        self.sensors[sid].update({
            "latest_value": value,
            "unit": unit,
            "status": status,
            "alarm": alarm,
            "monitored_asset": asset_id,
            "last_observed_turn": turn
        })

    def compress_events(self, max_events: int = 100):
        """Periodically compress bounded append-only event log into summary event."""
        if len(self.events) > max_events:
            older_events = self.events[:-50]
            recent_events = self.events[-50:]
            summary_event = {
                "event_id": "EVT-SUMMARY",
                "event_type": "EVENT_LOG_COMPRESSED",
                "severity": "INFO",
                "payload": {
                    "compressed_count": len(older_events),
                    "types_summarized": list(set(e.get("event_type") for e in older_events))
                }
            }
            self.events = [summary_event] + recent_events

    def get_asset_state(self, asset_id: str, state_key: str, default: Any = None) -> Any:
        aid = self.resolve_asset_id(asset_id)
        return self.assets.get(aid, {}).get(state_key, default)

    def get_sensor_telemetry(self, sensor_id: str, default: Any = None) -> Any:
        sid = self.resolve_asset_id(sensor_id)
        return self.latest_measurements.get(sid, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factory": self.factory,
            "agent": self.agent,
            "rooms": self.rooms,
            "assets": self.assets,
            "sensors": self.sensors,
            "relationships": self.relationships,
            "latest_measurements": self.latest_measurements,
            "event_count": len(self.events),
            "turn_count": len(self.action_history)
        }


