"""Entity, Relationship, State & Measurement Extraction module for FactoryMind."""

from typing import Dict, Any, List, Optional
from factorymind.config_loader import ConfigLoader

# Mapping of state words to state keys
STATE_KEY_MAP = {
    "RUNNING": "operational_state",
    "STOPPED": "operational_state",
    "NORMAL": "operational_state",
    "ENERGIZED": "energy_state",
    "DE_ENERGIZED": "energy_state",
    "OPEN": "access_state",
    "CLOSED": "access_state",
    "ENGAGED": "safety_state",
    "DISENGAGED": "safety_state",
    "ELEVATED_TEMPERATURE": "alarm",
    "SEVERE_VIBRATION": "alarm",
    "WARNING": "status",
    "CRITICAL": "status",
}

class FactExtractor:
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader

    def extract_entities(self, parsed_facts: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify known assets, sensors, and unresolved entity IDs from parsed facts."""
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})

        found_assets = set()
        found_sensors = set()
        unresolved = set()

        for fact in parsed_facts:
            extracted_ids = fact.get("extracted_ids", [])
            for eid in extracted_ids:
                if eid in assets_cfg:
                    found_assets.add(eid)
                elif eid in sensors_cfg:
                    found_sensors.add(eid)
                else:
                    unresolved.add(eid)

        return {
            "assets": sorted(list(found_assets)),
            "sensors": sorted(list(found_sensors)),
            "unresolved": sorted(list(unresolved))
        }

    def extract_relationships(self, parsed_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract explicit relationships (part_of, monitors, protects, controls, room) for entities mentioned."""
        entities = self.extract_entities(parsed_facts)
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})

        relationships = []
        for aid in entities["assets"]:
            adata = assets_cfg.get(aid, {})
            if "part_of" in adata:
                relationships.append({"source": aid, "relation": "part_of", "target": adata["part_of"]})
            if "protects" in adata:
                relationships.append({"source": aid, "relation": "protects", "target": adata["protects"]})
            if "controls" in adata:
                relationships.append({"source": aid, "relation": "controls", "target": adata["controls"]})
            if "room" in adata:
                relationships.append({"source": aid, "relation": "located_in", "target": adata["room"]})

        for sid in entities["sensors"]:
            sdata = sensors_cfg.get(sid, {})
            if "monitors" in sdata:
                relationships.append({"source": sid, "relation": "monitors", "target": sdata["monitors"]})
            if "room" in sdata:
                relationships.append({"source": sid, "relation": "located_in", "target": sdata["room"]})

        return relationships

    def extract_states(self, parsed_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract operational, energy, access, safety states, or alarms for entities in sentences."""
        extracted_states = []
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})

        # Collect all assets mentioned in the observation
        obs_assets = []
        for fact in parsed_facts:
            for eid in fact.get("extracted_ids", []):
                if eid in assets_cfg and eid not in obs_assets:
                    obs_assets.append(eid)

        primary_asset = obs_assets[0] if obs_assets else None
        current_asset = primary_asset

        for fact in parsed_facts:
            state_words = fact.get("state_words", [])
            extracted_ids = fact.get("extracted_ids", [])
            raw_evidence = fact.get("raw_evidence", "")

            # Update current asset if sentence contains an asset ID
            sentence_assets = [eid for eid in extracted_ids if eid in assets_cfg]
            if sentence_assets:
                current_asset = sentence_assets[0]

            if not state_words:
                continue

            # Determine target entities for the state
            target_entities = set()
            if sentence_assets:
                target_entities.update(sentence_assets)
                if primary_asset:
                    target_entities.add(primary_asset)
            elif current_asset:
                target_entities.add(current_asset)
                if primary_asset:
                    target_entities.add(primary_asset)
            elif obs_assets:
                target_entities.update(obs_assets)


            # Description matching fallback
            if not target_entities:
                for aid, adata in assets_cfg.items():
                    if adata.get("name", "").lower() in raw_evidence.lower():
                        target_entities.add(aid)
                for sid, sdata in sensors_cfg.items():
                    if sdata.get("name", "").lower() in raw_evidence.lower():
                        target_entities.add(sid)

            # Expand target entities to include controlling assets present in observation (e.g. PCS-CV01 controls CV-01)
            expanded_targets = set(target_entities)
            for target in target_entities:
                for aid in obs_assets:
                    adata = assets_cfg.get(aid, {})
                    if adata.get("controls") == target:
                        expanded_targets.add(aid)

            for target in expanded_targets:
                for word in state_words:
                    word_upper = word.upper()
                    state_key = STATE_KEY_MAP.get(word_upper, "state")
                    extracted_states.append({
                        "entity_id": target,
                        "state_key": state_key,
                        "value": word_upper,
                        "raw_evidence": raw_evidence
                    })


        return extracted_states



    def extract_measurements(self, parsed_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract numeric telemetry readings, map to sensors/assets, and evaluate domain thresholds."""
        measurements = []
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})
        thresholds_cfg = self.config_loader.thresholds.get("thresholds", {})

        current_sensor = None
        current_monitored = None

        # First pass to identify sensor in observation if present
        for fact in parsed_facts:
            for eid in fact.get("extracted_ids", []):
                if eid in sensors_cfg:
                    current_sensor = eid
                    current_monitored = sensors_cfg[eid].get("monitors")
                    break
            if current_sensor:
                break

        for fact in parsed_facts:
            numeric_readings = fact.get("numeric_readings", [])
            extracted_ids = fact.get("extracted_ids", [])
            raw_evidence = fact.get("raw_evidence", "")

            # Update current sensor if sentence contains a sensor ID
            for eid in extracted_ids:
                if eid in sensors_cfg:
                    current_sensor = eid
                    current_monitored = sensors_cfg[eid].get("monitors")
                    break

            if not numeric_readings:
                continue

            for val_str, unit in numeric_readings:
                try:
                    val = float(val_str)
                except ValueError:
                    continue

                # Check if this number is a threshold descriptor (e.g., "normal max: 70.0", "warning max: 80.0", "critical above: 80.0")
                # Look for preceding context in raw_evidence around the val_str
                pos = raw_evidence.lower().find(val_str)
                if pos != -1:
                    preceding = raw_evidence.lower()[:pos]
                    if any(kw in preceding[-30:] for kw in ["normal max", "warning max", "critical above", "threshold"]):
                        continue

                # Find associated sensor ID
                sensor_id = current_sensor
                monitored_asset = current_monitored

                if not sensor_id:
                    # Infer sensor from unit and asset ID in sentence
                    for eid in extracted_ids:
                        for sid, sdata in sensors_cfg.items():
                            if sdata.get("monitors") == eid and sdata.get("unit") == unit:
                                sensor_id = sid
                                monitored_asset = eid
                                break
                        if sensor_id:
                            break

                # Evaluate thresholds
                status = "NORMAL"
                limit_breached = None
                if monitored_asset and monitored_asset in thresholds_cfg:
                    asset_thresh = thresholds_cfg[monitored_asset]
                    # Find matching metric in threshold config (e.g. temperature_C or vibration_mm_s)
                    for metric_key, tdata in asset_thresh.items():
                        if isinstance(tdata, dict) and tdata.get("unit") == unit:
                            norm_max = tdata.get("normal_max")
                            warn_max = tdata.get("warning_max")
                            crit_above = tdata.get("critical_above")

                            if crit_above is not None and val >= crit_above:
                                status = "CRITICAL"
                                limit_breached = crit_above
                            elif warn_max is not None and val > warn_max:
                                status = "WARNING"
                                limit_breached = warn_max
                            elif norm_max is not None and val > norm_max:
                                status = "WARNING"
                                limit_breached = norm_max

                measurements.append({
                    "sensor_id": sensor_id,
                    "monitored_asset": monitored_asset,
                    "value": val,
                    "unit": unit,
                    "status": status,
                    "limit_breached": limit_breached,
                    "raw_evidence": raw_evidence
                })

        return measurements



