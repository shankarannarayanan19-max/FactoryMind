"""Phase 2 Deliverable Test: TextWorld World Authoring & Interactive Session."""

import pytest
from factorymind.environment_interface import TextWorldFactoryWorld, TextWorldSession

def test_gamemaker_world_creation():
    world_builder = TextWorldFactoryWorld()
    maker = world_builder.build_game()
    assert maker is not None

def test_turn_1_to_8_walkthrough():
    """Reproduces §18 Turn 1-8 walkthrough observation-for-observation."""
    session = TextWorldSession()

    # Turn 1: Initial Observation / Look
    obs1 = session.reset()
    assert "Packaging Bay 1 (ROOM-PACK-01)" in obs1
    assert "Conveyor Line 1 (CV-01)" in obs1
    assert "Tail Drive Motor & Bearing Assembly (CV-M02)" in obs1
    assert "Temperature Sensor (TS-CVM02-BRG)" in obs1
    assert "Vibration Sensor (VS-CVM02)" in obs1

    # Turn 2: inspect CV-01
    obs2 = session.act("inspect CV-01")
    assert "Conveyor Line 1 (CV-01)" in obs2
    assert "Packaging Bay 1 (ROOM-PACK-01)" in obs2
    assert "Main Drive Motor (CV-M01)" in obs2
    assert "Tail Drive Motor & Bearing Assembly (CV-M02)" in obs2
    assert "Operational state is RUNNING" in obs2
    assert "Energy state is ENERGIZED" in obs2

    # Turn 3: inspect CV-M02
    obs3 = session.act("inspect CV-M02")
    assert "Tail Drive Motor & Bearing Assembly (CV-M02)" in obs3
    assert "monitored by Temperature Sensor (TS-CVM02-BRG) and Vibration Sensor (VS-CVM02)" in obs3
    assert "Operational state is RUNNING" in obs3
    assert "Energy state is ENERGIZED" in obs3

    # Turn 4: read TS-CVM02-BRG
    obs4 = session.act("read TS-CVM02-BRG")
    assert "Temperature Sensor (TS-CVM02-BRG)" in obs4
    assert "Reading: 82.0 C" in obs4
    assert "Telemetry status: WARNING (ALARM: ELEVATED_TEMPERATURE)" in obs4

    # Turn 5: read VS-CVM02
    obs5 = session.act("read VS-CVM02")
    assert "Vibration Sensor (VS-CVM02)" in obs5
    assert "Reading: 5.8 mm/s" in obs5
    assert "Telemetry status: CRITICAL (ALARM: SEVERE_VIBRATION)" in obs5

    # Turn 6: request shutdown of CV-01
    obs6 = session.act("request shutdown of CV-01")
    assert "Shutdown request for Conveyor Line 1 (CV-01) processed by PLC Control Cabinet (PCS-CV01)" in obs6
    assert "Operational state updated to STOPPED" in obs6
    assert "Energy state updated to DE_ENERGIZED" in obs6

    # Turn 7: check PCS-CV01
    obs7 = session.act("check PCS-CV01")
    assert "PLC Control Cabinet (PCS-CV01)" in obs7
    assert "energy state is DE_ENERGIZED and operational state is STOPPED" in obs7

    # Turn 8: remove GUARD-CV01
    obs8 = session.act("remove GUARD-CV01")
    assert "Interlocked Safety Guard (GUARD-CV01)" in obs8
    assert "Access state is now OPEN" in obs8

def test_navigation():
    session = TextWorldSession()
    assert "ROOM-PACK-01" in session.current_room

    obs = session.act("go east")
    assert "Control Room 1 (ROOM-CTRL-01)" in obs
    assert session.current_room == "ROOM-CTRL-01"

    obs2 = session.act("go west")
    assert "Packaging Bay 1 (ROOM-PACK-01)" in obs2
    assert session.current_room == "ROOM-PACK-01"
