"""Phase 3 Deliverable Test: Preprocessing & Parsing."""

import pytest
from factorymind.parser import TextParser
from factorymind.config_loader import ConfigLoader

def test_unit_standardization_and_preprocessing():
    parser = TextParser()
    raw = "Temperature sensor TS-CVM02-BRG reads 82 deg C.\nVibration sensor VS-CVM02 reads 5.8 mm/sec."
    sentences = parser.preprocess(raw)

    assert len(sentences) == 2
    assert sentences[0]["raw_evidence"] == "Temperature sensor TS-CVM02-BRG reads 82 deg C."
    assert "82 C" in sentences[0]["normalized_text"]
    assert "5.8 mm/s" in sentences[1]["normalized_text"]

def test_room_detection_methods_and_confidences():
    parser = TextParser()

    # Tier 1: Explicit room sentence (confidence 1.0)
    obs1 = "Location: Packaging Bay 1 (ROOM-PACK-01)."
    room1 = parser.detect_room(obs1)
    assert room1["room"] == "ROOM-PACK-01"
    assert room1["confidence"] == 1.0
    assert room1["source"] == "deterministic_parser"

    # Tier 2: Navigation inference (confidence 0.90)
    obs2 = "You walk down the hallway."
    nav_intent = {"action": "go", "direction": "east"}
    room2 = parser.detect_room(obs2, nav_intent=nav_intent, prev_room="ROOM-PACK-01")
    assert room2["room"] == "ROOM-CTRL-01"
    assert room2["confidence"] == 0.90
    assert room2["source"] == "navigation_inference"

    # Tier 3: Unique asset-location evidence (confidence 0.85)
    obs3 = "Tail Drive Motor & Bearing Assembly (CV-M02) is running smoothly."
    room3 = parser.detect_room(obs3)
    assert room3["room"] == "ROOM-PACK-01"
    assert room3["confidence"] == 0.85
    assert room3["source"] == "asset_location_inference"

def test_impossible_transition_handling():
    parser = TextParser()

    # ROOM-PACK-01 and ROOM-MAINT-01 are connected (north-south)
    conflict_none = parser.check_impossible_transition("ROOM-PACK-01", "ROOM-MAINT-01")
    assert conflict_none is None

    # ROOM-CTRL-01 and ROOM-MAINT-01 are NOT directly connected in factory_map.yaml
    conflict = parser.check_impossible_transition("ROOM-CTRL-01", "ROOM-MAINT-01")
    assert conflict is not None
    assert conflict["event_type"] == "LOCATION_TRANSITION_CONFLICT"
    assert conflict["severity"] == "WARNING"
    assert "Impossible transition" in conflict["description"]

def test_llm_fallback_parsing():
    parser = TextParser()

    # Regular sentence matching regex
    parsed_regex = parser.parse_sentence({
        "raw_evidence": "TS-CVM02-BRG reading is 82 C.",
        "normalized_text": "TS-CVM02-BRG reading is 82 C."
    })
    assert parsed_regex["source"] == "deterministic_parser"
    assert parsed_regex["confidence"] == 1.0

    # Novel phrasing with no regex match at all -> calls LLM fallback
    parsed_llm = parser.parse_sentence({
        "raw_evidence": "the atmosphere feels unusually warm and humming faintly",
        "normalized_text": "the atmosphere feels unusually warm and humming faintly"
    })
    assert parsed_llm["source"] == "llm_fallback"
    assert parsed_llm["confidence"] == 0.50
    assert "llm_result" in parsed_llm
