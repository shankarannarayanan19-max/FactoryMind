"""Phase 5 Deliverable Test: Reconciliation & Persistent World Model Rules (§10 & §11)."""

import pytest
from factorymind.world_model import WorldModel
from factorymind.reconciler import Reconciler

def test_reconciliation_rule1_repetition():
    """Rule 1: Repeating information updates last_observed_turn & confidence without creating duplicate records."""
    reconciler = Reconciler()
    world_model = WorldModel()

    obs = "Conveyor Line 1 (CV-01) is running."
    reconciler.reconcile(world_model, obs, turn=1)

    initial_turn = world_model.assets["CV-01"]["last_observed_turn"]
    initial_conf = world_model.assets["CV-01"]["confidence"]
    asset_count_turn1 = len(world_model.assets)

    assert initial_turn == 1

    # Repeat exact same observation at turn 5
    reconciler.reconcile(world_model, obs, turn=5)

    assert world_model.assets["CV-01"]["last_observed_turn"] == 5
    assert world_model.assets["CV-01"]["confidence"] >= initial_conf
    assert len(world_model.assets) == asset_count_turn1  # No duplicate asset record created!

def test_reconciliation_rule2_state_history_and_health_degraded_event():
    """Rule 2: Dynamic state replacement preserves old values in state_history and emits ASSET_HEALTH_DEGRADED at turn 12."""
    reconciler = Reconciler()
    world_model = WorldModel()

    # Initial state: Normal temperature at turn 1
    reconciler.reconcile(world_model, "Temperature Sensor (TS-CVM02-BRG) reading is 65.0 C.", turn=1)
    assert world_model.assets["CV-M02"]["health_state"] == "NORMAL"

    # Turn 12: Degradation to WARNING (75.0 C exceeds 70.0 C normal_max)
    reconciler.reconcile(world_model, "Temperature Sensor (TS-CVM02-BRG) reading is 75.0 C.", turn=12)

    assert world_model.assets["CV-M02"]["health_state"] == "WARNING"
    assert len(world_model.assets["CV-M02"]["state_history"]) >= 1
    history_entry = world_model.assets["CV-M02"]["state_history"][-1]
    assert history_entry["old_value"] == "NORMAL"
    assert history_entry["new_value"] == "WARNING"
    assert history_entry["turn"] == 12

    # Assert exact ASSET_HEALTH_DEGRADED event from §10
    degraded_events = reconciler.event_engine.get_events(event_type="ASSET_HEALTH_DEGRADED")
    assert len(degraded_events) >= 1
    event = degraded_events[0]
    assert event["event_type"] == "ASSET_HEALTH_DEGRADED"
    assert event["payload"]["asset_id"] == "CV-M02"
    assert event["payload"]["old_health_state"] == "NORMAL"
    assert event["payload"]["new_health_state"] == "WARNING"
    assert event["turn"] == 12

def test_reconciliation_rule3_static_relationship_persistence():
    """Rule 3: Static relationships (part_of, located_in, monitors) persist across turns."""
    reconciler = Reconciler()
    world_model = WorldModel()

    reconciler.reconcile(world_model, "Conveyor Line 1 (CV-01) is running.", turn=1)

    part_of_rels = [r for r in world_model.relationships if r["source"] == "CV-M02" and r["relation"] == "part_of"]
    assert len(part_of_rels) >= 1
    assert part_of_rels[0]["target"] == "CV-01"

    # Turn 10: State changes to STOPPED, static relationship must persist!
    reconciler.reconcile(world_model, "request shutdown of CV-01", turn=10)

    part_of_rels_after = [r for r in world_model.relationships if r["source"] == "CV-M02" and r["relation"] == "part_of"]
    assert len(part_of_rels_after) >= 1
    assert part_of_rels_after[0]["target"] == "CV-01"

def test_reconciliation_rule4_contradiction_handling():
    """Rule 4: Contradicting measurements (82°C fixed vs 48°C portable) emit CONTRADICTS & SENSOR_VALIDATION_REQUIRED (never average)."""
    reconciler = Reconciler()
    world_model = WorldModel()

    # Step 1: Fixed sensor reading 82.0 C on TS-CVM02-BRG at turn 4
    reconciler.reconcile(world_model, "Temperature Sensor (TS-CVM02-BRG) reading is 82.0 C.", turn=4)

    fixed_val_before = world_model.latest_measurements["TS-CVM02-BRG"]["value"]
    assert fixed_val_before == 82.0

    # Step 2: Portable pyrometer reading 48.0 C on CV-M02 at turn 5
    portable_obs = "Measured temperature of CV-M02 with infrared_pyrometer is 48.0 C."
    reconciler.reconcile(world_model, portable_obs, turn=5)

    # Assert SENSOR_VALIDATION_REQUIRED status set on fixed sensor
    assert world_model.sensors["TS-CVM02-BRG"]["status"] == "SENSOR_VALIDATION_REQUIRED"

    # Assert CONTRADICTS relationship created
    contradict_rels = [r for r in world_model.relationships if r["relation"] == "CONTRADICTS"]
    assert len(contradict_rels) >= 1
    assert contradict_rels[0]["source"] == "TS-CVM02-BRG"

    # Assert SENSOR_CONTRADICTION event emitted
    contradict_events = reconciler.event_engine.get_events(event_type="SENSOR_CONTRADICTION")
    assert len(contradict_events) >= 1
    payload = contradict_events[0]["payload"]
    assert payload["fixed_value"] == 82.0
    assert payload["portable_value"] == 48.0

    # CRITICAL ASSERTION: Values are NEVER averaged to (82+48)/2 = 65.0!
    assert world_model.latest_measurements["TS-CVM02-BRG"]["value"] == 82.0
    assert world_model.latest_measurements["TS-CVM02-BRG"]["value"] != 65.0

def test_alias_deduplication():
    """Verifies that alias resolution ensures single physical asset record (§2 Step 2)."""
    world_model = WorldModel()

    id1 = world_model.resolve_asset_id("Tail Drive Motor & Bearing Assembly")
    id2 = world_model.resolve_asset_id("CV-M02")

    assert id1 == "CV-M02"
    assert id2 == "CV-M02"
    assert id1 == id2
    assert "CV-M02" in world_model.assets
    assert len([k for k in world_model.assets if k == "CV-M02"]) == 1
