"""Phase 8 Deliverable Test: Planner, Safety Validator & Executor (§15, §16, §17, §18 & §23)."""

import pytest
from factorymind.planner import Planner
from factorymind.safety_validator import SafetyValidator
from factorymind.executor import Executor
from factorymind.environment_interface import TextWorldSession
from factorymind.reconciler import Reconciler
from factorymind.world_model import WorldModel
from factorymind.information_analyser import InformationAnalyser
from factorymind.config_loader import ConfigLoader

def test_safety_validator_robot_cell_block():
    """Deliverable 1: The robot-cell entry / guard removal scenario from §16 reproduces the exact block reason and allowed_next_actions list."""
    validator = SafetyValidator()
    world_model = WorldModel()

    # Conveyor CV-01 is currently RUNNING and ENERGIZED
    world_model.update_asset_state("CV-01", "operational_state", "RUNNING")
    world_model.update_asset_state("CV-01", "energy_state", "ENERGIZED")

    # Attempt to remove protective guard while conveyor is running
    action_dict = {
        "goal": "remove_guard_for_direct_measurement",
        "proposed_action": "remove GUARD-CV01",
        "expected_destination": "ROOM-PACK-01",
        "reason": "Remove guard to measure temperature",
        "confidence": 1.0
    }

    validation_res = validator.validate(
        action_dict=action_dict,
        current_room="ROOM-PACK-01",
        inventory=["infrared_pyrometer"],
        world_model=world_model
    )

    # Assert exact §16 safety block schema
    assert validation_res["valid"] is False
    assert validation_res["safety_block"] is True
    assert validation_res["rule_id"] == "SR-GUARD-REMOVE"
    assert "de-energized and stopped" in validation_res["reason"].lower()
    
    preconditions = validation_res["required_preconditions"]
    assert any(p.get("asset") == "CV-01" and p.get("required_value") == "DE_ENERGIZED" for p in preconditions)

    assert "request shutdown of CV-01" in validation_res["allowed_next_actions"]

def test_end_to_end_walkthrough_loop():
    """Deliverable 2: The full turn-1-through-shutdown-request loop from §18 runs end-to-end using Phases 2–8 wired together via §23 architecture."""
    config_loader = ConfigLoader()
    config_loader.load_all()
    mission = config_loader.missions[0] if config_loader.missions else {}

    session = TextWorldSession(config_loader=config_loader)
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)
    planner = Planner()
    validator = SafetyValidator(config_loader=config_loader)
    executor = Executor()
    analyser = InformationAnalyser()

    inventory = ["infrared_pyrometer", "vibration_meter"]
    known_tool_locations = {"infrared_pyrometer": "ROOM-PACK-01"}

    # Initial turn 1 reset
    obs1 = session.reset()
    reconciler.reconcile(world_model, obs1, turn=1)
    assert world_model.agent["location"] == "ROOM-PACK-01"

    # End-to-End Loop Simulation (Turns 2 to 8)
    for turn in range(2, 9):
        current_room = world_model.agent["location"]
        gaps = analyser.find_missing_evidence(mission, world_model)

        # Step 1: Planner proposes action
        plan_action = planner.plan(
            current_room=current_room,
            mission=mission,
            inventory=inventory,
            missing_information=gaps["recommended_information_need"],
            known_tool_locations=known_tool_locations,
            world_model=world_model
        )

        # Step 2: Safety Validator gates action
        validation = validator.validate(
            action_dict=plan_action,
            current_room=current_room,
            inventory=inventory,
            world_model=world_model
        )

        # If safety block triggered, pivot to allowed next action
        if validation["safety_block"]:
            next_act = validation["allowed_next_actions"][0]
            plan_action = {
                "goal": "safety_mitigation",
                "proposed_action": next_act,
                "expected_destination": current_room,
                "reason": f"Safety block mitigated by rule {validation['rule_id']}",
                "confidence": 1.0
            }
            validation = validator.validate(
                action_dict=plan_action,
                current_room=current_room,
                inventory=inventory,
                world_model=world_model
            )
            assert validation["valid"] is True

        # Step 3: Executor executes action and reconciles into WorldModel
        exec_res = executor.execute(
            action_dict=plan_action,
            session=session,
            reconciler=reconciler,
            world_model=world_model,
            turn=turn
        )
        assert exec_res["observation"] is not None

    # End of walkthrough state assertions (§18)
    assert world_model.get_asset_state("CV-01", "operational_state") == "STOPPED"
    assert world_model.get_asset_state("CV-01", "energy_state") == "DE_ENERGIZED"
    assert world_model.get_asset_state("GUARD-CV01", "access_state") == "OPEN"
    assert len(world_model.action_history) >= 8
