"""Phase 0 Deliverable Test: Project Scaffold & Environment Validation."""

import os
import pytest

def test_textworld_import():
    import textworld
    assert textworld.__version__ is not None

def test_factorymind_modules_import():
    import factorymind
    from factorymind import (
        environment_interface,
        parser,
        extractor,
        reconciler,
        world_model,
        event_engine,
        information_analyser,
        query_engine,
        planner,
        safety_validator,
        executor,
        mission_checker,
        report_generator,
        llm_bridge,
    )
    assert factorymind.__version__ == "0.1.0"

def test_llm_bridge_completion():
    from factorymind.llm_bridge import LLMBridge
    bridge = LLMBridge(use_stub=True)
    facts = {"asset_id": "CV-M02", "health_state": "WARNING", "temperature_C": 82.0}
    narrative = bridge.narrate(facts)
    assert "CV-M02" in narrative or "WARNING" in narrative or "[Narrative Report]" in narrative

def test_config_files_exist():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_dir = os.path.join(base_dir, "config")
    expected_files = [
        "factory_map.yaml",
        "asset_registry.yaml",
        "sensor_registry.yaml",
        "safety_rules.yaml",
        "thresholds.yaml",
        "procedures.yaml",
        "missions.yaml",
    ]
    for fname in expected_files:
        fpath = os.path.join(config_dir, fname)
        assert os.path.exists(fpath), f"Missing config file: {fname}"
