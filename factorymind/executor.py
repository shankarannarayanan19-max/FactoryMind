"""Executor module converting validated actions into TextWorld commands."""

class Executor:
    def execute(self, action_dict: dict, session) -> str:
        command = action_dict.get("proposed_action", "look")
        return session.act(command)
