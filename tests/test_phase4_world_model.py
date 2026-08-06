"""Phase 4 Deliverable Test: Fact Extraction, Event Engine & World Model Reconciliation."""

import pytest
from factorymind.world_model import WorldModel
from factorymind.event_engine import EventEngine
from factorymind.extractor import FactExtractor
from factorymind.reconciler import Reconciler
from factorymind.parser import TextParser
from factorymind.environment_interface import TextWorldSession

def test_fact_extractor_entities_and_states():
    extractor = FactExtractor()
    parser = TextParser()

    obs = (
        "Conveyor Line 1 (CV-01) is running smoothly. "
        "Tail Drive Motor & Bearing Assembly (CV-M02) operational state is RUNNING and energy state is ENERGIZED."
    )
    parsed_obs = parser.parse_observation(obs)
    
    entities = extractor.extract_entities(parsed_obs["parsed_facts"])
    assert "CV-01" in entities["assets"]
    assert "CV-M02" in entities["assets"]
    assert len(entities["unresolved"]) == 0

    relationships = extractor.extract_relationships(parsed_obs["parsed_facts"])
    assert any(r["source"] == "CV-M02" and r["target"] == "CV-01" and r["relation"] == "part_of" for r in relationships)

    states = extractor.extract_states(parsed_obs["parsed_facts"])
    assert any(s["entity_id"] == "CV-01" and s["value"] == "RUNNING" for s in states)
    assert any(s["entity_id"] == "CV-M02" and s["state_key"] == "energy_state" and s["value"] == "ENERGIZED" for s in states)

def test_event_engine_emission_and_taxonomy():
    event_engine = EventEngine()
    
    evt1 = event_engine.emit("LOCATION_TRANSITION_CONFLICT", {"description": "Conflict"}, severity="WARNING", turn=1)
    evt2 = event_engine.emit("SENSOR_MEASUREMENT", {"value": 82.0}, severity="INFO", turn=2)
    evt3 = event_engine.emit("THRESHOLD_BREACH", {"limit": 70.0}, severity="WARNING", turn=2)

    assert evt1["event_id"] == "EVT-00001"
    assert len(event_engine.event_log) == 3

    warnings = event_engine.get_events(severity="WARNING")
    assert len(warnings) == 2
    assert set(e["event_type"] for e in warnings) == {"LOCATION_TRANSITION_CONFLICT", "THRESHOLD_BREACH"}

def test_threshold_evaluation_and_events():
    reconciler = Reconciler()
    world_model = WorldModel()

    # Temperature reading 75.0 C on TS-CVM02-BRG -> exceeds 70.0 C normal_max -> WARNING breach
    obs_temp_warn = "Temperature Sensor (TS-CVM02-BRG) reading is 75.0 C."
    reconciler.reconcile(world_model, obs_temp_warn, turn=1)

    assert "TS-CVM02-BRG" in world_model.latest_measurements
    telemetry_warn = world_model.latest_measurements["TS-CVM02-BRG"]
    assert telemetry_warn["value"] == 75.0
    assert telemetry_warn["status"] == "WARNING"

    breach_events = reconciler.event_engine.get_events(event_type="THRESHOLD_BREACH", severity="WARNING")
    assert len(breach_events) >= 1

    # Temperature reading 82.0 C on TS-CVM02-BRG -> exceeds 80.0 C critical_above -> CRITICAL breach
    obs_temp_crit = "Temperature Sensor (TS-CVM02-BRG) reading is 82.0 C."
    reconciler.reconcile(world_model, obs_temp_crit, turn=2)

    assert world_model.latest_measurements["TS-CVM02-BRG"]["value"] == 82.0
    assert world_model.latest_measurements["TS-CVM02-BRG"]["status"] == "CRITICAL"

    # Vibration reading 5.8 mm/s on VS-CVM02 -> exceeds 4.5 mm/s critical_above -> CRITICAL breach
    obs_vib = "Vibration Sensor (VS-CVM02) reading is 5.8 mm/s."
    reconciler.reconcile(world_model, obs_vib, turn=3)

    assert "VS-CVM02" in world_model.latest_measurements
    telemetry_vib = world_model.latest_measurements["VS-CVM02"]
    assert telemetry_vib["value"] == 5.8
    assert telemetry_vib["status"] == "CRITICAL"

    critical_breaches = reconciler.event_engine.get_events(event_type="THRESHOLD_BREACH", severity="CRITICAL")
    assert len(critical_breaches) >= 2


def test_unresolved_entity_warning():
    reconciler = Reconciler()
    world_model = WorldModel()

    obs_unknown = "Auxiliary Pump PUMP-99 is displaying error code ERR-01."
    reconciler.reconcile(world_model, obs_unknown, turn=1)

    unresolved_events = reconciler.event_engine.get_events(event_type="UNRESOLVED_ENTITY")
    assert len(unresolved_events) >= 1
    assert any(e["payload"]["entity_id"] == "PUMP-99" for e in unresolved_events)

def test_multi_turn_walkthrough_reconciliation():
    """Validates persistent WorldModel state progression across interactive Turn 1-8 walkthrough."""
    session = TextWorldSession()
    reconciler = Reconciler()
    world_model = WorldModel()

    # Turn 1: Initial look
    obs1 = session.reset()
    reconciler.reconcile(world_model, obs1, turn=1)
    assert world_model.agent["location"] == "ROOM-PACK-01"

    # Turn 2: inspect CV-01
    obs2 = session.act("inspect CV-01")
    reconciler.reconcile(world_model, obs2, turn=2)
    assert world_model.get_asset_state("CV-01", "operational_state") == "RUNNING"
    assert world_model.get_asset_state("CV-01", "energy_state") == "ENERGIZED"

    # Turn 3: inspect CV-M02
    obs3 = session.act("inspect CV-M02")
    reconciler.reconcile(world_model, obs3, turn=3)
    assert world_model.get_asset_state("CV-M02", "operational_state") == "RUNNING"

    # Turn 4: read TS-CVM02-BRG
    obs4 = session.act("read TS-CVM02-BRG")
    reconciler.reconcile(world_model, obs4, turn=4)
    assert world_model.latest_measurements["TS-CVM02-BRG"]["value"] == 82.0
    assert world_model.latest_measurements["TS-CVM02-BRG"]["status"] in ("WARNING", "CRITICAL")

    # Turn 5: read VS-CVM02
    obs5 = session.act("read VS-CVM02")
    reconciler.reconcile(world_model, obs5, turn=5)
    assert world_model.latest_measurements["VS-CVM02"]["value"] == 5.8
    assert world_model.latest_measurements["VS-CVM02"]["status"] == "CRITICAL"

    # Turn 6: request shutdown of CV-01
    obs6 = session.act("request shutdown of CV-01")
    reconciler.reconcile(world_model, obs6, turn=6)
    assert world_model.get_asset_state("CV-01", "operational_state") == "STOPPED"
    assert world_model.get_asset_state("CV-01", "energy_state") == "DE_ENERGIZED"

    # Turn 7: check PCS-CV01
    obs7 = session.act("check PCS-CV01")
    reconciler.reconcile(world_model, obs7, turn=7)
    assert world_model.get_asset_state("PCS-CV01", "energy_state") == "DE_ENERGIZED"

    # Turn 8: remove GUARD-CV01
    obs8 = session.act("remove GUARD-CV01")
    reconciler.reconcile(world_model, obs8, turn=8)
    assert world_model.get_asset_state("GUARD-CV01", "access_state") == "OPEN"

    # Verify event engine accumulated history
    assert len(world_model.events) > 10
    assert len(world_model.measurement_history) == 2
    assert len(world_model.action_history) == 8
