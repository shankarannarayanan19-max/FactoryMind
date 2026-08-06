"""Deterministic Safety Validator module for FactoryMind enforcing deterministic safety rules (§16).

Hard Rule: 100% deterministic and unit-testable. Safety critical.
"""

from typing import Dict, Any, List, Optional
from factorymind.world_model import WorldModel
from factorymind.config_loader import ConfigLoader

class SafetyValidator:
    """Deterministic safety validator executing the §16 8-step validation sequence."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader

    def validate(
        self,
        action_dict: Dict[str, Any],
        current_room: str,
        inventory: List[str],
        world_model: WorldModel
    ) -> Dict[str, Any]:
        """Validate proposed planner action using exact 8-step sequence (§16).
        Return schema:
        {"valid": bool, "safety_block": bool, "rule_id": str, "reason": str, "required_preconditions": list, "allowed_next_actions": list}
        """
        proposed_action = action_dict.get("proposed_action", "").strip()

        # Helper response generator
        def allow_response(rule_id: str = "SR-ALLOW", reason: str = "Action validated successfully"):
            return {
                "valid": True,
                "safety_block": False,
                "rule_id": rule_id,
                "reason": reason,
                "required_preconditions": [],
                "allowed_next_actions": [proposed_action]
            }

        def block_response(rule_id: str, reason: str, preconditions: List[Dict[str, Any]], next_actions: List[str]):
            return {
                "valid": False,
                "safety_block": True,
                "rule_id": rule_id,
                "reason": reason,
                "required_preconditions": preconditions,
                "allowed_next_actions": next_actions
            }

        # Step 1: Command Recognition Check
        valid_verbs = ["look", "go", "inspect", "read", "remove", "request shutdown of", "check", "measure"]
        recognized = any(proposed_action.startswith(v) for v in valid_verbs)
        if not recognized:
            return block_response(
                rule_id="SR-INVALID-CMD",
                reason=f"Unrecognised command syntax: '{proposed_action}'",
                preconditions=[],
                next_actions=["look"]
            )

        # Step 2: Room / Visibility Check
        if proposed_action.startswith("inspect ") or proposed_action.startswith("check ") or proposed_action.startswith("remove ") or proposed_action.startswith("read "):
            words = proposed_action.split()
            target_id = words[-1]
            target_room = None
            if target_id in world_model.assets:
                target_room = world_model.assets[target_id].get("room")
            elif target_id in world_model.sensors:
                target_room = world_model.sensors[target_id].get("room")

            if target_room and target_room != current_room and target_id not in inventory:
                return block_response(
                    rule_id="SR-VISIBILITY",
                    reason=f"Target {target_id} is located in {target_room}, not visible in current room {current_room}.",
                    preconditions=[{"room": target_room, "state_key": "location", "required_value": target_room}],
                    next_actions=[f"go {target_room}"]
                )

        # Step 3: Tool Availability Check
        if proposed_action.startswith("measure "):
            if "with " in proposed_action:
                tool_name = proposed_action.split("with ")[-1].strip()
                if tool_name not in inventory:
                    return block_response(
                        rule_id="SR-TOOL-MISSING",
                        reason=f"Required tool '{tool_name}' is not carried in inventory.",
                        preconditions=[{"inventory": tool_name, "state_key": "carried", "required_value": True}],
                        next_actions=["go ROOM-CTRL-01"]
                    )

        # Step 4: Energy State Check (SR-GUARD-REMOVE)
        if "remove GUARD" in proposed_action or "remove_guard" in proposed_action:
            cv01_energy = world_model.get_asset_state("CV-01", "energy_state", "ENERGIZED")
            cv01_op = world_model.get_asset_state("CV-01", "operational_state", "RUNNING")

            if cv01_energy == "ENERGIZED" or cv01_op == "RUNNING":
                return block_response(
                    rule_id="SR-GUARD-REMOVE",
                    reason="Conveyor must be de-energized and stopped before removing protective guard.",
                    preconditions=[
                        {"asset": "CV-01", "state_key": "energy_state", "required_value": "DE_ENERGIZED"},
                        {"asset": "PCS-CV01", "state_key": "operational_state", "required_value": "STOPPED"}
                    ],
                    next_actions=["request shutdown of CV-01"]
                )

        # Step 5: Guards / Access State Check (SR-PORTABLE-MEASURE)
        if proposed_action.startswith("measure "):
            guard_access = world_model.get_asset_state("GUARD-CV01", "access_state", "CLOSED")
            if guard_access == "CLOSED":
                return block_response(
                    rule_id="SR-PORTABLE-MEASURE",
                    reason="Guard must be opened/removed to take direct contact thermal measurement.",
                    preconditions=[
                        {"asset": "GUARD-CV01", "state_key": "access_state", "required_value": "OPEN"}
                    ],
                    next_actions=["remove GUARD-CV01"]
                )

        # Step 6: Authorization Check (SR-SHUTDOWN-REQUEST)
        if proposed_action.startswith("request shutdown of"):
            return allow_response(
                rule_id="SR-SHUTDOWN-REQUEST",
                reason="Shutdown request authorized for anomaly mitigation."
            )

        # Step 7: Mission Restrictions Check
        prohibited = action_dict.get("prohibited_actions", [])
        if "remove_guard_while_running" in prohibited and "remove GUARD" in proposed_action:
            cv01_op = world_model.get_asset_state("CV-01", "operational_state", "RUNNING")
            if cv01_op == "RUNNING":
                return block_response(
                    rule_id="SR-PROHIBITED-ACTION",
                    reason="Prohibited mission action: cannot remove guard while machinery is running.",
                    preconditions=[{"asset": "CV-01", "state_key": "operational_state", "required_value": "STOPPED"}],
                    next_actions=["request shutdown of CV-01"]
                )

        # Step 8: Allow Decision
        return allow_response()
