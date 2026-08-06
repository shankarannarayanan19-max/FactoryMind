"""Planner module for heuristic navigation and action planning."""

class Planner:
    def plan(self, current_room: str, mission: dict, inventory: list, missing_info: list, known_tools: dict) -> dict:
        return {
            "goal": "inspect",
            "proposed_action": "look",
            "expected_destination": current_room,
            "reason": "initial inspection",
            "confidence": 1.0
        }
