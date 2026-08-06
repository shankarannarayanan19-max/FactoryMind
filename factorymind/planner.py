"""Planner module for FactoryMind implementing heuristic navigation and action planning (§15).

Hard Rule: Pure rule/heuristic logic — no LLM involved.
"""

from typing import Dict, Any, List, Optional
from factorymind.world_model import WorldModel

class Planner:
    """Heuristic planner proposing actions to fulfill missing information needs (§15)."""

    def plan(
        self,
        current_room: str,
        mission: Dict[str, Any],
        inventory: List[str],
        missing_information: List[str],
        known_tool_locations: Dict[str, str],
        world_model: Optional[WorldModel] = None
    ) -> Dict[str, Any]:
        """Propose next action adhering strictly to §15 output contract:
        {"goal": str, "proposed_action": str, "expected_destination": str, "reason": str, "confidence": float}
        """
        turn_count = len(world_model.action_history) if world_model else 0

        # Heuristic 1: Turn 0 / initial inspection
        if turn_count == 0:
            return {
                "goal": "initial_inspection",
                "proposed_action": "look",
                "expected_destination": current_room,
                "reason": "Perform initial room scan to identify assets and sensors",
                "confidence": 1.0
            }

        # Retrieve information gaps if missing_information list is strings
        missing_needs = missing_information if isinstance(missing_information, list) else []

        # Heuristic 2: Verify elevated temperature or vibration anomaly
        if any("temperature" in gap or "pyrometer" in gap for gap in missing_needs):
            guard_state = world_model.get_asset_state("GUARD-CV01", "access_state", "CLOSED") if world_model else "CLOSED"
            cv01_energy = world_model.get_asset_state("CV-01", "energy_state", "ENERGIZED") if world_model else "ENERGIZED"
            cv01_op = world_model.get_asset_state("CV-01", "operational_state", "RUNNING") if world_model else "RUNNING"

            # Step 2a: If guard is CLOSED, check if conveyor is de-energized/stopped
            if guard_state == "CLOSED":
                if cv01_energy == "ENERGIZED" or cv01_op == "RUNNING":
                    return {
                        "goal": "de_energize_conveyor_for_guard_removal",
                        "proposed_action": "request shutdown of CV-01",
                        "expected_destination": current_room,
                        "reason": "Conveyor must be stopped and de-energized before removing protective safety guard",
                        "confidence": 1.0
                    }
                else:
                    return {
                        "goal": "remove_guard_for_direct_measurement",
                        "proposed_action": "remove GUARD-CV01",
                        "expected_destination": current_room,
                        "reason": "Remove protective guard to gain physical access for direct thermal measurement",
                        "confidence": 1.0
                    }

            # Step 2b: If guard is OPEN, verify tool availability and take direct measurement
            if guard_state == "OPEN":
                if "infrared_pyrometer" in inventory:
                    return {
                        "goal": "direct_temperature_measurement",
                        "proposed_action": "measure temperature of CV-M02 with infrared_pyrometer",
                        "expected_destination": current_room,
                        "reason": "Perform direct surface pyrometer measurement on CV-M02 bearing housing",
                        "confidence": 1.0
                    }
                else:
                    tool_room = known_tool_locations.get("infrared_pyrometer", "ROOM-CTRL-01")
                    return {
                        "goal": "fetch_measurement_tool",
                        "proposed_action": f"go {tool_room}",
                        "expected_destination": tool_room,
                        "reason": f"Retrieve infrared_pyrometer from {tool_room}",
                        "confidence": 0.9
                    }

        # Heuristic 3: Asset inspection sequence (Turn 2-5 walkthrough)
        cv01_op = world_model.get_asset_state("CV-01", "operational_state") if world_model else None
        if not cv01_op:
            return {
                "goal": "inspect_conveyor_line",
                "proposed_action": "inspect CV-01",
                "expected_destination": current_room,
                "reason": "Inspect primary material transport conveyor line CV-01",
                "confidence": 1.0
            }

        cvm02_op = world_model.get_asset_state("CV-M02", "operational_state") if world_model else None
        if not cvm02_op:
            return {
                "goal": "inspect_tail_motor",
                "proposed_action": "inspect CV-M02",
                "expected_destination": current_room,
                "reason": "Inspect tail drive motor and bearing assembly CV-M02",
                "confidence": 1.0
            }

        ts_reading = world_model.get_sensor_telemetry("TS-CVM02-BRG") if world_model else None
        if not ts_reading:
            return {
                "goal": "read_temperature_sensor",
                "proposed_action": "read TS-CVM02-BRG",
                "expected_destination": current_room,
                "reason": "Read tail bearing temperature sensor telemetry TS-CVM02-BRG",
                "confidence": 1.0
            }

        vs_reading = world_model.get_sensor_telemetry("VS-CVM02") if world_model else None
        if not vs_reading:
            return {
                "goal": "read_vibration_sensor",
                "proposed_action": "read VS-CVM02",
                "expected_destination": current_room,
                "reason": "Read tail motor vibration sensor telemetry VS-CVM02",
                "confidence": 1.0
            }

        # Heuristic 4: Verify PLC Control Cabinet after shutdown
        pcs_state = world_model.get_asset_state("PCS-CV01", "energy_state") if world_model else None
        if cv01_op == "STOPPED" and not pcs_state:
            return {
                "goal": "verify_plc_cabinet",
                "proposed_action": "check PCS-CV01",
                "expected_destination": current_room,
                "reason": "Verify PLC control cabinet panel confirms stopped and de-energized status",
                "confidence": 1.0
            }

        # Fallback default plan
        return {
            "goal": "routine_inspection",
            "proposed_action": "look",
            "expected_destination": current_room,
            "reason": "Maintain room observation and monitor telemetry",
            "confidence": 0.8
        }

