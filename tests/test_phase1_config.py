"""Phase 1 Deliverable Test: Scenario Configuration & Schema Validation."""

import os
import tempfile
import yaml
import pytest
from factorymind.config_loader import ConfigLoader

def test_load_canonical_conveyor_scenario():
    loader = ConfigLoader()
    configs = loader.load_all()

    # Assert rooms
    assert "ROOM-PACK-01" in configs["factory_map"]["rooms"]
    assert "ROOM-CTRL-01" in configs["factory_map"]["rooms"]

    # Assert assets
    assets = configs["asset_registry"]["assets"]
    assert "CV-01" in assets
    assert "CV-M01" in assets
    assert "CV-M02" in assets
    assert "GUARD-CV01" in assets
    assert "PCS-CV01" in assets
    assert assets["CV-M02"]["part_of"] == "CV-01"

    # Assert sensors
    sensors = configs["sensor_registry"]["sensors"]
    assert "TS-CVM02-BRG" in sensors
    assert "VS-CVM02" in sensors
    assert sensors["TS-CVM02-BRG"]["monitors"] == "CV-M02"

    # Assert thresholds
    thresholds = configs["thresholds"]["thresholds"]
    assert "CV-M02" in thresholds
    assert thresholds["CV-M02"]["temperature_C"]["normal_max"] == 70.0

    # Assert safety rules & missions
    assert len(configs["safety_rules"]) >= 3
    assert len(configs["missions"]) >= 1
    assert configs["missions"][0]["mission_id"] == "MIS-CV01-INSPECT"

def test_dangling_room_reference_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid configs except asset with dangling room
        with open(os.path.join(tmpdir, "factory_map.yaml"), "w") as f:
            yaml.dump({"rooms": {"ROOM-A": {"name": "Room A"}}}, f)
        with open(os.path.join(tmpdir, "asset_registry.yaml"), "w") as f:
            yaml.dump({"assets": {"AST-01": {"room": "NON_EXISTENT_ROOM"}}}, f)
        with open(os.path.join(tmpdir, "sensor_registry.yaml"), "w") as f:
            yaml.dump({"sensors": {}}, f)
        with open(os.path.join(tmpdir, "thresholds.yaml"), "w") as f:
            yaml.dump({"thresholds": {}}, f)
        with open(os.path.join(tmpdir, "safety_rules.yaml"), "w") as f:
            yaml.dump({"safety_rules": []}, f)
        with open(os.path.join(tmpdir, "procedures.yaml"), "w") as f:
            yaml.dump({"procedures": {}}, f)
        with open(os.path.join(tmpdir, "missions.yaml"), "w") as f:
            yaml.dump({"missions": []}, f)

        loader = ConfigLoader(config_dir=tmpdir)
        with pytest.raises(ValueError, match="unknown room"):
            loader.load_all()

def test_orphan_sensor_monitor_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "factory_map.yaml"), "w") as f:
            yaml.dump({"rooms": {"ROOM-A": {"name": "Room A"}}}, f)
        with open(os.path.join(tmpdir, "asset_registry.yaml"), "w") as f:
            yaml.dump({"assets": {"AST-01": {"room": "ROOM-A"}}}, f)
        with open(os.path.join(tmpdir, "sensor_registry.yaml"), "w") as f:
            yaml.dump({"sensors": {"SNS-01": {"monitors": "NON_EXISTENT_ASSET"}}}, f)
        with open(os.path.join(tmpdir, "thresholds.yaml"), "w") as f:
            yaml.dump({"thresholds": {}}, f)
        with open(os.path.join(tmpdir, "safety_rules.yaml"), "w") as f:
            yaml.dump({"safety_rules": []}, f)
        with open(os.path.join(tmpdir, "procedures.yaml"), "w") as f:
            yaml.dump({"procedures": {}}, f)
        with open(os.path.join(tmpdir, "missions.yaml"), "w") as f:
            yaml.dump({"missions": []}, f)

        loader = ConfigLoader(config_dir=tmpdir)
        with pytest.raises(ValueError, match="unknown asset"):
            loader.load_all()

def test_unknown_safety_rule_action_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "factory_map.yaml"), "w") as f:
            yaml.dump({"rooms": {"ROOM-A": {"name": "Room A"}}}, f)
        with open(os.path.join(tmpdir, "asset_registry.yaml"), "w") as f:
            yaml.dump({"assets": {}}, f)
        with open(os.path.join(tmpdir, "sensor_registry.yaml"), "w") as f:
            yaml.dump({"sensors": {}}, f)
        with open(os.path.join(tmpdir, "thresholds.yaml"), "w") as f:
            yaml.dump({"thresholds": {}}, f)
        with open(os.path.join(tmpdir, "safety_rules.yaml"), "w") as f:
            yaml.dump({"safety_rules": [{"rule_id": "SR-BAD", "action": "fly_to_moon"}]}, f)
        with open(os.path.join(tmpdir, "procedures.yaml"), "w") as f:
            yaml.dump({"procedures": {}}, f)
        with open(os.path.join(tmpdir, "missions.yaml"), "w") as f:
            yaml.dump({"missions": []}, f)

        loader = ConfigLoader(config_dir=tmpdir)
        with pytest.raises(ValueError, match="unknown action"):
            loader.load_all()
