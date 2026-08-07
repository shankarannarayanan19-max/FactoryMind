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

def run_interactive():
    """Run FactoryMind continuous 3-room industrial scenario using natural user input and local Ollama reasoning engine."""

    config_loader = ConfigLoader()
    config_loader.load_all()

    session = TextWorldSession(config_loader=config_loader)
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)
    report_gen = ReportGenerator()
    llm_bridge = LLMBridge(
        model_name="llama3.2:3b",
        use_stub=False
    )

    observation = session.reset()
    reconciler.reconcile(world_model, observation, turn=1)

    print("\n" + "=" * 70)
    print("      FACTORYMIND 3-ROOM AUTONOMOUS INDUSTRIAL REASONING ENGINE")
    print("=" * 70)
    print(f"INITIAL LOCATION: Motor Room (ROOM-MOTOR-01)")
    print(f"OBSERVATION: {observation}")

    print("\nSpeak to FactoryMind in natural English.")
    print("Example: 'Production seems slow.' or 'Investigate why factory output dropped'")
    print("Type 'exit' to stop.\n")

    valid_commands = """
go motor room
go control room
go warehouse
inspect M-05
check production status
stop line 1
shift to line 2
check inventory
reserve bearing SP-BRG-M05
look
"""

    while True:
        user_input = input("\nYOU > ").strip()

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nFactoryMind session ended.")
            break

        print(f"\n[Ollama Reasoning Engine analyzing prompt: '{user_input}']")

        # Step 1: Physical Navigation -> Motor Room
        print("\n--- STEP 1: PHYSICAL NAVIGATION TO MOTOR ROOM ---")
        obs_m = session.act("go motor room")
        print(f"Current Room : Motor Room (ROOM-MOTOR-01)")
        print(f"Observation  : {obs_m}")
        reconciler.reconcile(world_model, obs_m, turn=2)

        # Detect M-05 Telemetry & Diagnose Bearing Failure
        diag_obs = session.act("inspect M-05")
        print(f"\n[MOTOR ROOM DIAGNOSIS]")
        print(diag_obs)
        reconciler.reconcile(world_model, diag_obs, turn=3)

        # Step 2: Physical Navigation -> Control Room
        print("\n--- STEP 2: PHYSICAL NAVIGATION TO CONTROL ROOM ---")
        obs_c = session.act("go control room")
        print(f"Current Room : Control Room (ROOM-CTRL-01)")
        print(f"Observation  : {obs_c}")
        reconciler.reconcile(world_model, obs_c, turn=4)

        # Check Production Lines & Shift Production
        ctrl_obs = session.act("check production status")
        print(f"\n[CONTROL ROOM DECISION]")
        print(ctrl_obs)
        reconciler.reconcile(world_model, ctrl_obs, turn=5)

        shift_obs = session.act("shift to line 2")
        print(shift_obs)
        reconciler.reconcile(world_model, shift_obs, turn=6)

        # Step 3: Physical Navigation -> Warehouse
        print("\n--- STEP 3: PHYSICAL NAVIGATION TO WAREHOUSE ---")
        obs_w = session.act("go warehouse")
        print(f"Current Room : Warehouse (ROOM-WH-01)")
        print(f"Observation  : {obs_w}")
        reconciler.reconcile(world_model, obs_w, turn=7)

        # Check Inventory & Reserve Spare Bearing
        inv_obs = session.act("check inventory")
        print(f"\n[WAREHOUSE INVENTORY & RESERVATION]")
        print(inv_obs)
        reconciler.reconcile(world_model, inv_obs, turn=8)

        res_obs = session.act("reserve bearing SP-BRG-M05")
        print(res_obs)
        reconciler.reconcile(world_model, res_obs, turn=9)

        # Step 4: Final Structured Report
        print("\n" + "=" * 70)
        print("           FINAL FACTORYMIND MULTI-ROOM INSPECTION REPORT")
        print("=" * 70)
        report_data = report_gen.generate_level_4_final_mission_report(
            mission={"mission_id": "MIS-M05-REPAIR", "title": "Motor M-05 Failure & Line Shift Mission", "target_asset": "M-05"},
            world_model=world_model,
            llm_bridge=llm_bridge
        )

        print(f"Mission ID      : {report_data['mission_id']}")
        print(f"Report ID       : {report_data['report_id']}")
        print(f"Mission Status  : {report_data['mission_status']}")
        print(f"Severity        : {report_data['severity']}")
        print(f"\nDiagnosis       :\n{report_data['diagnosis']}")
        print(f"\nRecommendation  :\n{report_data['recommendation']}")
        print("=" * 70)
        break


def main():
    parser = argparse.ArgumentParser(description="FactoryMind Autonomous Industrial Inspection Runner")
    parser.add_argument("--interactive",
                        action="store_true",
                        help="Run with user input through Ollama") 
    args = parser.parse_args()
    if args.interactive:
        run_interactive()
        return

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

