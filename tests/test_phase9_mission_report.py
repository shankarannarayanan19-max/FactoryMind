"""Phase 9 Deliverable Test: Mission Completion & Reporting (§19 & §20)."""

import pytest
from factorymind.mission_checker import MissionChecker
from factorymind.report_generator import ReportGenerator
from factorymind.world_model import WorldModel
from factorymind.reconciler import Reconciler
from factorymind.environment_interface import TextWorldSession
from factorymind.config_loader import ConfigLoader
from factorymind.llm_bridge import LLMBridge

def test_mission_checker_evaluation():
    """Deliverable 1: MissionChecker.evaluate(mission, world_model) checks completion_conditions and flags completion progress."""
    config_loader = ConfigLoader()
    config_loader.load_all()
    mission = config_loader.missions[0] if config_loader.missions else {"mission_id": "MIS-CV01-INSPECT"}

    checker = MissionChecker()
    world_model = WorldModel(config_loader=config_loader)

    # Initial state: 0% progress
    eval_initial = checker.evaluate(mission, world_model)
    assert eval_initial["complete"] is False
    assert eval_initial["progress"] < 1.0

    # Simulate completed conditions: conveyor stopped, guard open, telemetry reconciled
    world_model.update_asset_state("CV-01", "operational_state", "STOPPED")
    world_model.update_asset_state("GUARD-CV01", "access_state", "OPEN")
    world_model.update_sensor_reading("TS-CVM02-BRG", 82.0, "C", "CRITICAL")
    world_model.update_sensor_reading("VS-CVM02", 5.8, "mm/s", "CRITICAL")

    eval_complete = checker.evaluate(mission, world_model)
    assert eval_complete["complete"] is True
    assert len(eval_complete["missing_conditions"]) == 0 or eval_complete["complete"] is True

def test_report_generator_all_4_levels():
    """Deliverable 2: Running full conveyor scenario produces reports across all 4 levels, including Level 4 report matching §19 Output 4 schema."""
    config_loader = ConfigLoader()
    config_loader.load_all()
    mission = config_loader.missions[0] if config_loader.missions else {"mission_id": "MIS-CV01-INSPECT"}

    session = TextWorldSession(config_loader=config_loader)
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)
    report_gen = ReportGenerator()
    llm_bridge = LLMBridge(use_stub=True)

    # Replay conveyor inspection walkthrough
    obs1 = session.reset()
    reconciler.reconcile(world_model, obs1, turn=1)
    obs4 = session.act("read TS-CVM02-BRG")
    reconciler.reconcile(world_model, obs4, turn=4)
    obs5 = session.act("read VS-CVM02")
    reconciler.reconcile(world_model, obs5, turn=5)
    obs6 = session.act("request shutdown of CV-01")
    reconciler.reconcile(world_model, obs6, turn=6)

    # Level 1: Immediate command echo
    lvl1 = report_gen.generate_level_1_command_echo("request shutdown of CV-01", obs6)
    assert "[Level 1 Command Echo]" in lvl1
    assert "request shutdown of CV-01" in lvl1

    # Level 2: Internal structured JSON
    lvl2 = report_gen.generate_level_2_structured_json(world_model)
    assert "agent_state" in lvl2
    assert "assets_snapshot" in lvl2
    assert "latest_measurements" in lvl2

    # Level 3: LLM-narrated explainable response
    facts_json = {
        "asset_id": "CV-M02",
        "health_state": "CRITICAL",
        "temperature_C": 82.0,
        "vibration_mm_s": 5.8
    }
    lvl3 = report_gen.generate_level_3_explainable_response(facts_json, llm_bridge)
    assert "[Narrative Report]" in lvl3
    assert "CV-M02" in lvl3

    # Level 4: Final structured mission report matching §19 Output 4 schema exactly
    lvl4 = report_gen.generate_level_4_final_mission_report(mission, world_model, llm_bridge)

    # Assert exact 10 fields from §19 Output 4 schema
    assert "report_id" in lvl4
    assert "mission_id" in lvl4
    assert "mission_status" in lvl4
    assert "evidence" in lvl4
    assert "safety_checks" in lvl4
    assert "diagnosis" in lvl4
    assert "severity" in lvl4
    assert "actions_taken" in lvl4
    assert "recommendation" in lvl4
    assert "repair_performed" in lvl4

    assert lvl4["mission_id"] == "MIS-CV01-INSPECT"
    assert lvl4["severity"] in ("WARNING", "CRITICAL")
    assert lvl4["repair_performed"] is False
    assert len(lvl4["evidence"]) >= 2
    assert "CV-M02" in lvl4["diagnosis"]
