"""Mission Checker evaluating completion conditions."""

class MissionChecker:
    def evaluate(self, mission: dict, world_model) -> dict:
        return {
            "complete": False,
            "progress": 0.0,
            "missing_conditions": mission.get("completion_conditions", [])
        }
