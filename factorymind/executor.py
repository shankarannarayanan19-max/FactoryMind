"""Executor module for FactoryMind executing validated actions (§17 & §23)."""

from typing import Dict, Any, Optional
from factorymind.environment_interface import TextWorldSession
from factorymind.reconciler import Reconciler
from factorymind.world_model import WorldModel

class Executor:
    """Executes validated planner actions against TextWorld session and passes observation to Reconciler (§17 & §23)."""

    def execute(
        self,
        action_dict: Dict[str, Any],
        session: TextWorldSession,
        reconciler: Reconciler,
        world_model: WorldModel,
        turn: int = 0
    ) -> Dict[str, Any]:
        """Execute validated planner action against environment session and reconcile world state (§17)."""
        cmd = action_dict.get("proposed_action", "look").strip()
        nav_intent = None

        if cmd.startswith("go "):
            direction = cmd.split("go ")[-1].strip()
            nav_intent = {"action": "go", "direction": direction}

        # Step 1: Call TextWorld environment
        observation = session.act(cmd)

        # Step 2: Reconcile observation into persistent WorldModel (Phase 3 -> Phase 4/5)
        recon_result = reconciler.reconcile(
            world_model=world_model,
            observation=observation,
            nav_intent=nav_intent,
            turn=turn
        )

        return {
            "command": cmd,
            "observation": observation,
            "reconciliation": recon_result,
            "turn": turn
        }
