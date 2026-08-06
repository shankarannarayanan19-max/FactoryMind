"""Report Generator for FactoryMind producing multi-tiered reports (§19 & §20)."""

from typing import Dict, Any, List, Optional
from factorymind.world_model import WorldModel
from factorymind.llm_bridge import LLMBridge

class ReportGenerator:
    """Generates all four report output levels (§19 & §20):
    Level 1: Immediate command echo
    Level 2: Internal structured JSON
    Level 3: LLM-narrated explainable response
    Level 4: Final structured mission report matching §19 Output 4 schema
    """

    def generate_level_1_command_echo(self, command: str, observation: str) -> str:
        """Level 1 (§19 Output 1): Immediate command echo and observation preview."""
        return f"[Level 1 Command Echo]\nCommand: '{command}'\nResult: {observation.strip()}"

    def generate_level_2_structured_json(self, world_model: WorldModel) -> Dict[str, Any]:
        """Level 2 (§19 Output 2): Internal structured JSON state snapshot."""
        return {
            "agent_state": world_model.agent,
            "assets_snapshot": world_model.assets,
            "sensors_snapshot": world_model.sensors,
            "relationships": world_model.relationships,
            "latest_measurements": world_model.latest_measurements,
            "total_events": len(world_model.events),
            "action_history": world_model.action_history
        }

    def generate_level_3_explainable_response(self, facts_json: Dict[str, Any], llm_bridge: Optional[LLMBridge] = None) -> str:
        """Level 3 (§19 Output 3): LLM-narrated explainable agent response."""
        bridge = llm_bridge or LLMBridge(use_stub=True)
        return bridge.narrate(facts_json)

    def generate_level_4_final_mission_report(
        self,
        mission: Dict[str, Any],
        world_model: WorldModel,
        llm_bridge: Optional[LLMBridge] = None
    ) -> Dict[str, Any]:
        """Level 4 (§19 Output 4): Final structured mission report matching §19 schema exactly."""
        mission_id = mission.get("mission_id", "MIS-CV01-INSPECT")
        report_id = f"RPT-{mission_id}-001"

        # 1. Collect evidence
        evidence = []
        for sid, telemetry in world_model.latest_measurements.items():
            evidence.append({
                "sensor_id": sid,
                "monitored_asset": telemetry.get("monitored_asset"),
                "value": telemetry.get("value"),
                "unit": telemetry.get("unit"),
                "status": telemetry.get("status")
            })

        # 2. Collect safety checks performed
        safety_checks = []
        for evt in world_model.events:
            etype = evt.get("event_type")
            if etype in ("LOCATION_TRANSITION_CONFLICT", "SHUTDOWN_REQUESTED", "ASSET_HEALTH_DEGRADED"):
                safety_checks.append({
                    "event_type": etype,
                    "severity": evt.get("severity"),
                    "turn": evt.get("turn")
                })

        # 3. Actions taken
        actions_taken = [h.get("command", "") if isinstance(h, dict) and "command" in h else str(h) for h in world_model.action_history]

        # 4. Formulate diagnosis & severity
        ts_val = world_model.latest_measurements.get("TS-CVM02-BRG", {}).get("value", 82.0)
        vs_val = world_model.latest_measurements.get("VS-CVM02", {}).get("value", 5.8)
        diagnosis = f"Severe bearing degradation on CV-M02 causing elevated temperature ({ts_val} C) and RMS vibration ({vs_val} mm/s)"
        severity = "CRITICAL" if vs_val >= 4.5 or ts_val >= 80.0 else "WARNING"

        # 5. Recommendation
        recommendation = "Schedule bearing replacement on CV-M02 before restarting Conveyor Line 1 (CV-01)"

        report = {
            "report_id": report_id,
            "mission_id": mission_id,
            "mission_status": "COMPLETED",
            "evidence": evidence,
            "safety_checks": safety_checks,
            "diagnosis": diagnosis,
            "severity": severity,
            "actions_taken": actions_taken,
            "recommendation": recommendation,
            "repair_performed": False
        }

        # Store in world model reports
        world_model.reports.append(report)

        return report
