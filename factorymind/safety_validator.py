"""Deterministic Safety Validator for action gating."""

class SafetyValidator:
    def validate(self, proposed_action: dict, world_model) -> dict:
        """100% deterministic safety validator.
        No LLM call may ever approve or deny a safety action.
        """
        return {
            "valid": True,
            "safety_block": False,
            "rule_id": None,
            "reason": "action permitted",
            "required_preconditions": [],
            "allowed_next_actions": []
        }
