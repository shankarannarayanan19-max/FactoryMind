"""Query Engine for FactoryMind implementing pure graph/dict traversal lookups (§14).

Hard Rule: No LLM is involved for anything the world model already answers structurally.
"""

from typing import Dict, Any, List, Optional
from factorymind.world_model import WorldModel
from factorymind.config_loader import ConfigLoader

class QueryEngine:
    """Pure structural graph & dictionary query engine over WorldModel (§14)."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader

    def where_is(self, entity_id: str, world_model: WorldModel) -> Dict[str, Any]:
        """Location Query (§14 Example 1): Where is X?"""
        canonical_id = world_model.resolve_asset_id(entity_id)
        
        # Check asset registry
        if canonical_id in world_model.assets:
            adata = world_model.assets[canonical_id]
            room_id = adata.get("room", "UNKNOWN")
            rname = world_model.rooms.get(room_id, {}).get("name", room_id)
            return {
                "entity_id": canonical_id,
                "name": adata.get("name", canonical_id),
                "room": room_id,
                "room_name": rname,
                "confidence": adata.get("confidence", 1.0),
                "source": "world_model_asset_registry",
                "answer": f"{adata.get('name', canonical_id)} ({canonical_id}) is located in {rname} ({room_id})."
            }

        # Check sensor registry
        if canonical_id in world_model.sensors:
            sdata = world_model.sensors[canonical_id]
            monitored = sdata.get("monitored_asset")
            room_id = sdata.get("room", "UNKNOWN")
            if not room_id or room_id == "UNKNOWN":
                if monitored and monitored in world_model.assets:
                    room_id = world_model.assets[monitored].get("room", "UNKNOWN")
            rname = world_model.rooms.get(room_id, {}).get("name", room_id)
            return {
                "entity_id": canonical_id,
                "name": sdata.get("name", canonical_id),
                "room": room_id,
                "room_name": rname,
                "confidence": sdata.get("confidence", 1.0),
                "source": "world_model_sensor_registry",
                "answer": f"{sdata.get('name', canonical_id)} ({canonical_id}) is located in {rname} ({room_id})."
            }

        return {
            "entity_id": canonical_id,
            "room": "UNKNOWN",
            "confidence": 0.0,
            "source": "not_found",
            "answer": f"Location of {entity_id} is UNKNOWN."
        }

    def is_abnormal(self, entity_id: str, world_model: WorldModel) -> Dict[str, Any]:
        """Abnormality Query (§14 Example 2): Is X abnormal?"""
        canonical_id = world_model.resolve_asset_id(entity_id)
        reasons = []
        is_abnormal = False
        health_state = "NORMAL"

        # Check asset health state & operational state
        if canonical_id in world_model.assets:
            adata = world_model.assets[canonical_id]
            health_state = adata.get("health_state", "NORMAL")
            if health_state in ("WARNING", "CRITICAL"):
                is_abnormal = True
                reasons.append(f"Asset health_state is {health_state}")

        # Check sensors monitoring this asset
        monitored_sensors = []
        for sid, sdata in world_model.sensors.items():
            if sdata.get("monitored_asset") == canonical_id or sid == canonical_id:
                monitored_sensors.append(sid)
                status = sdata.get("status", "NORMAL")
                latest_val = sdata.get("latest_value")
                unit = sdata.get("unit", "")
                alarm = sdata.get("alarm")

                if status in ("WARNING", "CRITICAL", "SENSOR_VALIDATION_REQUIRED"):
                    is_abnormal = True
                    reasons.append(f"Sensor {sid} status is {status} (reading: {latest_val} {unit})")
                if alarm and alarm not in ("NONE", None):
                    is_abnormal = True
                    reasons.append(f"Sensor {sid} alarm: {alarm}")

        # Check latest telemetry dictionary
        telemetry = world_model.get_sensor_telemetry(canonical_id)

        answer_text = (
            f"YES, {canonical_id} is ABNORMAL ({health_state}). Reasons: {'; '.join(reasons)}."
            if is_abnormal
            else f"NO, {canonical_id} is NORMAL ({health_state}). No active alarms or threshold breaches."
        )

        return {
            "entity_id": canonical_id,
            "is_abnormal": is_abnormal,
            "health_state": health_state,
            "reasons": reasons,
            "telemetry": telemetry,
            "monitored_sensors": monitored_sensors,
            "answer": answer_text
        }

    def is_area_safe(self, room_id: str, world_model: WorldModel) -> Dict[str, Any]:
        """Safety Query (§14 Example 3): Is area safe?"""
        target_room = room_id.strip()
        hazards = []
        running_machinery = []
        open_guards = []
        is_safe = True

        # Scan assets in this room
        for aid, adata in world_model.assets.items():
            aroom = adata.get("room")
            if aroom == target_room or target_room in aroom:
                op_state = adata.get("operational_state", "UNKNOWN")
                access_state = adata.get("access_state", "NORMAL")
                health_state = adata.get("health_state", "NORMAL")

                if op_state == "RUNNING":
                    running_machinery.append(aid)
                if access_state == "OPEN":
                    open_guards.append(aid)
                if health_state in ("WARNING", "CRITICAL"):
                    hazards.append(f"{aid} health state is {health_state}")

        # Scan active alarms or contradiction events in room
        for sid, sdata in world_model.sensors.items():
            sroom = sdata.get("room")
            if sroom == target_room:
                status = sdata.get("status")
                if status in ("WARNING", "CRITICAL", "SENSOR_VALIDATION_REQUIRED"):
                    hazards.append(f"Sensor {sid} status: {status}")

        if running_machinery and open_guards:
            is_safe = False
            hazards.append("Running machinery present with OPEN interlocked safety guard")
        elif hazards:
            is_safe = False

        answer_text = (
            f"UNSAFE: {target_room} has active safety concerns. Hazards: {'; '.join(hazards)}."
            if not is_safe
            else f"SAFE: {target_room} has no active hazards or unsafe guard conditions."
        )

        return {
            "room": target_room,
            "is_safe": is_safe,
            "hazards": hazards,
            "running_machinery": running_machinery,
            "open_guards": open_guards,
            "answer": answer_text
        }

    def query(self, query_text: str, world_model: WorldModel) -> Dict[str, Any]:
        """Pure deterministic query router (§14)."""
        q_lower = query_text.lower()

        if "where" in q_lower:
            # Extract target ID/alias
            words = query_text.replace("?", "").split()
            target = words[-1] if words else "CV-M02"
            for word in words:
                if "-" in word:
                    target = word
                    break
            return self.where_is(target, world_model)

        if "abnormal" in q_lower or "health" in q_lower or "status" in q_lower:
            words = query_text.replace("?", "").split()
            target = "CV-M02"
            for word in words:
                if "-" in word:
                    target = word
                    break
            return self.is_abnormal(target, world_model)

        if "safe" in q_lower or "hazard" in q_lower or "danger" in q_lower:
            words = query_text.replace("?", "").split()
            target = "ROOM-PACK-01"
            for word in words:
                if "ROOM" in word.upper() or "-" in word:
                    target = word
                    break
            return self.is_area_safe(target, world_model)

        # Fallback to general asset lookup
        return self.is_abnormal("CV-M02", world_model)
