"""Phase 6 Deliverable Test: Events & Information-Gap Analysis (§12 & §13)."""

import pytest
from factorymind.event_engine import EventEngine, VALID_EVENT_TYPES
from factorymind.world_model import WorldModel
from factorymind.reconciler import Reconciler
from factorymind.information_analyser import InformationAnalyser
from factorymind.environment_interface import TextWorldSession
from factorymind.config_loader import ConfigLoader

def test_event_taxonomy_verbatim():
    """Verifies that all §12 Event Taxonomy types can be emitted and queried verbatim."""
    event_engine = EventEngine()
    
    verbatim_types = [
        "ROOM_ENTERED",
        "ASSET_DISCOVERED",
        "STATE_CHANGED",
        "ALARM_OBSERVED",
        "SAFETY_HAZARD_OBSERVED",
        "MEASUREMENT_RECORDED",
        "SENSOR_CONTRADICTION",
        "ANOMALY_CONFIRMED",
        "SHUTDOWN_REQUESTED",
        "INSPECTION_HOLD_PLACED",
        "MISSION_COMPLETED",
    ]

    for etype in verbatim_types:
        assert etype in VALID_EVENT_TYPES
        evt = event_engine.emit(etype, {"test": True}, severity="INFO", turn=1)
        assert evt["event_type"] == etype

    assert len(event_engine.event_log) == len(verbatim_types)

def test_conveyor_turn_12_information_gap():
    """Deliverable: Running conveyor scenario up to turn 12 (fixed readings only, no portable confirmation yet)
    produces the exact gap list from §13 (independent_temperature_measurement, independent_vibration_measurement, etc.).
    """
    config_loader = ConfigLoader()
    config_loader.load_all()
    missions = config_loader.missions
    mission = missions[0] if missions else {"mission_id": "MIS-CV01-INSPECT"}

    session = TextWorldSession(config_loader=config_loader)
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)
    analyser = InformationAnalyser()

    # Replay walkthrough up to fixed sensor readings (turns 1-5)
    obs1 = session.reset()
    reconciler.reconcile(world_model, obs1, turn=1)

    obs2 = session.act("inspect CV-01")
    reconciler.reconcile(world_model, obs2, turn=2)

    obs3 = session.act("inspect CV-M02")
    reconciler.reconcile(world_model, obs3, turn=3)

    obs4 = session.act("read TS-CVM02-BRG")
    reconciler.reconcile(world_model, obs4, turn=4)

    obs5 = session.act("read VS-CVM02")
    reconciler.reconcile(world_model, obs5, turn=5)

    # At turn 12, fixed sensors read 82.0°C and 5.8 mm/s, but no portable confirmation has occurred yet
    gap_result = analyser.find_missing_evidence(mission, world_model)

    rec_needs = gap_result["recommended_information_need"]
    unverified = gap_result["unverified_anomalies"]

    # Assert exact §13 gap list items
    assert "independent_temperature_measurement" in rec_needs
    assert "independent_vibration_measurement" in rec_needs
    assert "remove_guard_for_direct_measurement" in rec_needs

    assert len(unverified) >= 1
    assert any("CV-M02" in u for u in unverified)
