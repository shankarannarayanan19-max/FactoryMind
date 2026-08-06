"""Information Analyser for FactoryMind finding missing evidence and information needs (§13)."""

from typing import Dict, Any, List, Optional
from factorymind.world_model import WorldModel

class InformationAnalyser:
    """Evaluates world model coverage against mission requirements and identifies information gaps (§13)."""

    def find_missing_evidence(self, mission: Dict[str, Any], world_model: WorldModel) -> Dict[str, Any]:
        """Compare mission required tasks / completion conditions against current world-model coverage.
        Returns recommended_information_need list exactly as in §13.
        """
        missing_information: List[str] = []
        recommended_information_need: List[str] = []
        unverified_anomalies: List[str] = []

        # 1. Analyze unverified telemetry anomalies (e.g., TS-CVM02-BRG reading elevated temp without portable confirmation)
        for sid, sdata in world_model.sensors.items():
            status = sdata.get("status", "NORMAL")
            latest_val = sdata.get("latest_value")
            monitored = sdata.get("monitored_asset", "UNKNOWN")
            stype = sdata.get("sensor_type", "TELEMETRY").upper()

            if status in ("WARNING", "CRITICAL") or (latest_val is not None and latest_val > 70.0):
                unverified_anomalies.append(f"{monitored} elevated {stype.lower()} ({status})")

                # Check if an independent portable tool measurement has been taken for this asset and sensor type
                has_portable_confirmation = False
                for m in world_model.measurement_history:
                    raw_ev = m.get("raw_evidence", "").lower()
                    m_asset = m.get("monitored_asset")
                    if m_asset == monitored or m_asset == sid:
                        if "pyrometer" in raw_ev or "meter" in raw_ev or "tool" in raw_ev:
                            has_portable_confirmation = True
                            break

                if not has_portable_confirmation:
                    if stype == "TEMPERATURE" or "temp" in sid.lower() or "brg" in sid.lower():
                        if "independent_temperature_measurement" not in recommended_information_need:
                            recommended_information_need.append("independent_temperature_measurement")
                        missing_information.append(f"Portable pyrometer temperature verification on {monitored}")
                    
                    if stype == "VIBRATION" or "vib" in sid.lower() or "vs" in sid.lower():
                        if "independent_vibration_measurement" not in recommended_information_need:
                            recommended_information_need.append("independent_vibration_measurement")
                        missing_information.append(f"Portable vibration meter verification on {monitored}")

        # 2. Check physical access prerequisites (e.g. guard status for direct contact measurement)
        if "independent_temperature_measurement" in recommended_information_need or "independent_vibration_measurement" in recommended_information_need:
            guard_state = world_model.get_asset_state("GUARD-CV01", "access_state", "CLOSED")
            if guard_state == "CLOSED":
                if "remove_guard_for_direct_measurement" not in recommended_information_need:
                    recommended_information_need.append("remove_guard_for_direct_measurement")
                missing_information.append("Interlocked safety guard GUARD-CV01 removal")

        # 3. Calculate coverage percentage based on completion conditions
        conditions = mission.get("completion_conditions", [])
        met_count = 0
        for cond in conditions:
            if isinstance(cond, str):
                cond_upper = cond.upper()
                if cond in world_model.mission_state or any(e.get("event_type") == cond_upper for e in world_model.events):
                    met_count += 1
            elif isinstance(cond, dict):
                asset = cond.get("asset")
                skey = cond.get("state_key")
                req_val = cond.get("required_value")
                curr_val = world_model.get_asset_state(asset, skey)
                if curr_val == req_val:
                    met_count += 1

        coverage = (met_count / len(conditions) * 100.0) if conditions else 0.0


        return {
            "missing_information": missing_information,
            "recommended_information_need": recommended_information_need,
            "unverified_anomalies": unverified_anomalies,
            "coverage_percentage": coverage
        }
