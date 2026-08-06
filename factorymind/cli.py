"""CLI Entry Point & Standalone Mission Runner for FactoryMind (§23).

Usage:
    python -m factorymind.cli --mission MIS-CV01-INSPECT --auto --report-level 4
"""

import sys
import argparse
from typing import Dict, Any, Optional
from factorymind.config_loader import ConfigLoader
from factorymind.environment_interface import TextWorldSession
from factorymind.reconciler import Reconciler
from factorymind.world_model import WorldModel
from factorymind.information_analyser import InformationAnalyser
from factorymind.planner import Planner
from factorymind.safety_validator import SafetyValidator
from factorymind.executor import Executor
from factorymind.mission_checker import MissionChecker
from factorymind.report_generator import ReportGenerator
from factorymind.llm_bridge import LLMBridge

def run_mission(
    mission_id: str = "MIS-CV01-INSPECT",
    auto: bool = True,
    max_turns: int = 15,
    report_level: int = 4
) -> Dict[str, Any]:
    """Run FactoryMind mission loop (§23 architecture) and return report."""
    config_loader = ConfigLoader()
    config_loader.load_all()

    # Find mission config
    mission = None
    for m in config_loader.missions:
        if m.get("mission_id") == mission_id:
            mission = m
            break
    if not mission:
        mission = config_loader.missions[0] if config_loader.missions else {"mission_id": mission_id}

    session = TextWorldSession(config_loader=config_loader)
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)
    analyser = InformationAnalyser()
    planner = Planner()
    validator = SafetyValidator(config_loader=config_loader)
    executor = Executor()
    checker = MissionChecker()
    report_gen = ReportGenerator()
    llm_bridge = LLMBridge(
    model_name="llama3.2:3b",
    use_stub=False
)
    inventory = ["infrared_pyrometer", "vibration_meter"]
    known_tool_locations = {"infrared_pyrometer": "ROOM-PACK-01"}

    # Turn 1: Reset environment
    obs1 = session.reset()
    reconciler.reconcile(world_model, obs1, turn=1)

    for turn in range(2, max_turns + 1):
        current_room = world_model.agent.get("location", "ROOM-PACK-01")
        gaps = analyser.find_missing_evidence(mission, world_model)

        # Plan action
        plan_action = planner.plan(
            current_room=current_room,
            mission=mission,
            inventory=inventory,
            missing_information=gaps["recommended_information_need"],
            known_tool_locations=known_tool_locations,
            world_model=world_model
        )

        # Validate action
        validation = validator.validate(
            action_dict=plan_action,
            current_room=current_room,
            inventory=inventory,
            world_model=world_model
        )

        if validation["safety_block"]:
            next_act = validation["allowed_next_actions"][0]
            plan_action = {
                "goal": "safety_mitigation",
                "proposed_action": next_act,
                "expected_destination": current_room,
                "reason": f"Mitigate safety block rule {validation['rule_id']}",
                "confidence": 1.0
            }

        # Execute action
        executor.execute(
            action_dict=plan_action,
            session=session,
            reconciler=reconciler,
            world_model=world_model,
            turn=turn
        )

        # Check completion
        eval_res = checker.evaluate(mission, world_model)
        if eval_res["complete"]:
            break

    # Generate requested report level
    if report_level == 1:
        last_cmd = world_model.action_history[-1]["observation"] if world_model.action_history else "look"
        output = {"level": 1, "text": report_gen.generate_level_1_command_echo(last_cmd, obs1)}
    elif report_level == 2:
        output = {"level": 2, "json": report_gen.generate_level_2_structured_json(world_model)}
    elif report_level == 3:
        facts = {"asset_id": "CV-M02", "health_state": "CRITICAL", "turn": len(world_model.action_history)}
        output = {"level": 3, "text": report_gen.generate_level_3_explainable_response(facts, llm_bridge)}
    else:
        output = {"level": 4, "report": report_gen.generate_level_4_final_mission_report(mission, world_model, llm_bridge)}

    return output

def main():
    parser = argparse.ArgumentParser(description="FactoryMind Autonomous Industrial Inspection Runner")
    parser.add_argument("--mission", type=str, default="MIS-CV01-INSPECT", help="Mission ID to execute")
    parser.add_argument("--auto", action="store_true", default=True, help="Run autonomously to completion")
    parser.add_argument("--max-turns", type=int, default=15, help="Maximum execution turns")
    parser.add_argument("--report-level", type=int, default=4, choices=[1, 2, 3, 4], help="Report level to output")
    args = parser.parse_args()

    res = run_mission(
        mission_id=args.mission,
        auto=args.auto,
        max_turns=args.max_turns,
        report_level=args.report_level
    )
    if "report" in res:
        report = res["report"]
        print("\n" + "=" * 70)
        print("               FACTORYMIND AI INSPECTION REPORT")
        print("=" * 70)

        print(f"Mission ID      : {report['mission_id']}")
        print(f"Report ID       : {report['report_id']}")
        print(f"Mission Status  : {report['mission_status']}")
        print(f"Severity        : {report['severity']}")

        print("\nDiagnosis")
        print("-" * 70)
        print(report["diagnosis"])

        print("\nRecommendation")
        print("-" * 70)
        print(report["recommendation"])

        print("\nEvidence")
        print("-" * 70)

        for evidence in report.get("evidence", []):
            print(f"Sensor  : {evidence['sensor_id']}")
            print(f"Asset   : {evidence['monitored_asset']}")
            print(f"Reading : {evidence['value']} {evidence['unit']}")
            print(f"Status  : {evidence['status']}")
            print()

        print("Safety Events")
        print("-" * 70)

        for event in report.get("safety_checks", []):
            print(
                f"Turn {event.get('turn', 0)} | "
                f"{event.get('event_type', '')} | "
                f"{event.get('severity', '')}"
            )

        print("\nRepair Performed :", report.get("repair_performed", False))
        print("=" * 70)
    else:
        print("=== FactoryMind Mission Execution Result ===")
        print(res)

if __name__ == "__main__":
    main()

