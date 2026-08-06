"""Phase 11 Deliverable Test: Standalone Packaging & CLI Entry Point (§23)."""

import pytest
from factorymind.cli import run_mission

def test_cli_autonomous_mission_execution():
    """Deliverable: CLI entry point executes autonomous mission loop (§23 architecture) and produces Level 4 final mission report."""
    res = run_mission(mission_id="MIS-CV01-INSPECT", auto=True, max_turns=12, report_level=4)

    assert res["level"] == 4
    report = res["report"]

    assert report["mission_id"] == "MIS-CV01-INSPECT"
    assert report["mission_status"] == "COMPLETED"
    assert report["severity"] in ("WARNING", "CRITICAL")
    assert "report_id" in report
    assert "evidence" in report
    assert "diagnosis" in report
    assert "actions_taken" in report
    assert "recommendation" in report
    assert report["repair_performed"] is False
