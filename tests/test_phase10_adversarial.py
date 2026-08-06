"""Phase 10 Deliverable Test: Error Handling & Adversarial Test Suite (§10, §14, §16, §21 & §22)."""

import pytest
from factorymind.config_loader import ConfigLoader
from factorymind.world_model import WorldModel
from factorymind.reconciler import Reconciler
from factorymind.llm_bridge import LLMBridge
from factorymind.parser import TextParser



def test_typo_alias_resolution():
    """Test 1: Alias & variant name resolution maps typos/aliases to canonical asset IDs."""
    config_loader = ConfigLoader()
    config_loader.load_all()
    world_model = WorldModel(config_loader=config_loader)

    # Resolve variants
    assert world_model.resolve_asset_id("Tail Drive Motor") == "CV-M02"
    assert world_model.resolve_asset_id("CV-M02") == "CV-M02"
    assert world_model.resolve_asset_id("Conveyor Line 1") == "CV-01"

def test_unrecognized_entity_distractor():
    """Test 2: Unrecognized entities / distractor text in observation emit UNRESOLVED_ENTITY event without crashing."""
    config_loader = ConfigLoader()
    config_loader.load_all()
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)

    distractor_obs = "Ghost Pump (PUMP-99) observed leaking unknown fluid in room UNKNOWN-BAY."
    result = reconciler.reconcile(world_model, distractor_obs, turn=1)

    # Assert UNRESOLVED_ENTITY event was emitted
    unresolved_events = [e for e in world_model.events if e.get("event_type") == "UNRESOLVED_ENTITY"]
    assert len(unresolved_events) >= 1
    assert any("PUMP-99" in e["payload"]["entity_id"] for e in unresolved_events)

def test_sensor_contradiction_rule4():
    """Test 3: Portable pyrometer (48°C) vs fixed telemetry sensor (82°C) sets status to SENSOR_VALIDATION_REQUIRED and emits SENSOR_CONTRADICTION event without averaging."""
    config_loader = ConfigLoader()
    config_loader.load_all()
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)

    # Fixed sensor reading 82°C
    obs_fixed = "Temperature Sensor (TS-CVM02-BRG) reading is 82.0 C."
    reconciler.reconcile(world_model, obs_fixed, turn=4)

    # Portable pyrometer reading 48°C
    obs_portable = "Measured temperature of CV-M02 with infrared_pyrometer reading 48.0 C."
    reconciler.reconcile(world_model, obs_portable, turn=5)

    # Assert SENSOR_VALIDATION_REQUIRED and SENSOR_CONTRADICTION event
    sensor_data = world_model.sensors.get("TS-CVM02-BRG")
    assert sensor_data["status"] == "SENSOR_VALIDATION_REQUIRED"

    contradiction_events = [e for e in world_model.events if e.get("event_type") == "SENSOR_CONTRADICTION"]
    assert len(contradiction_events) >= 1

    # Assert values were NEVER averaged (fixed sensor remains 82.0)
    assert sensor_data["latest_value"] == 82.0

def test_malformed_config_validation():
    """Test 4: Missing configuration or invalid YAML references raise descriptive ValueError validation errors."""
    loader = ConfigLoader()
    loader.load_all()

    # Inject unknown room reference in asset registry
    loader.asset_registry["assets"]["CV-01"]["room"] = "NONEXISTENT-ROOM"
    with pytest.raises(ValueError, match="unknown room"):
        loader.validate()



def test_hallucination_defense():
    """Test 5: LLM bridge hallucination defense rejects distractor numbers not present in input facts JSON."""
    bridge = LLMBridge(use_stub=True)

    facts_json = {
        "entity_id": "CV-M02",
        "health_state": "CRITICAL",
        "latest_measurements": {"value": 82.0, "unit": "C"}
    }

    # Extract valid numbers
    valid_nums = bridge._extract_all_numbers(facts_json)
    assert "82.0" in valid_nums or "82" in valid_nums
    assert "999.9" not in valid_nums

    # Generated narration MUST NOT include distractor number 999.9
    narrative = bridge.narrate(facts_json)
    assert "999.9" not in narrative
