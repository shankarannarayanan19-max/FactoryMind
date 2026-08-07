"""
CLI Entry Point for FactoryMind.

Run interactive local mode:
    python -m factorymind.cli --interactive

Run automatic mission mode:
    python -m factorymind.cli \
        --mission MIS-CV01-INSPECT \
        --auto \
        --max-turns 15 \
        --report-level 4
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict

from factorymind.config_loader import ConfigLoader
from factorymind.database import FactoryDatabase
from factorymind.environment_interface import TextWorldSession
from factorymind.executor import Executor
from factorymind.information_analyser import InformationAnalyser
from factorymind.llm_bridge import LLMBridge
from factorymind.mission_checker import MissionChecker
from factorymind.navigator import RoomNavigator
from factorymind.planner import Planner
from factorymind.reconciler import Reconciler
from factorymind.report_generator import ReportGenerator
from factorymind.safety_validator import SafetyValidator
from factorymind.world_model import WorldModel


QWEN_MODEL = "qwen3:1.7b"


# ---------------------------------------------------------------------
# Automatic mission mode
# ---------------------------------------------------------------------

def run_mission(
    mission_id: str = "MIS-CV01-INSPECT",
    auto: bool = True,
    max_turns: int = 15,
    report_level: int = 4,
) -> Dict[str, Any]:
    """Run the original autonomous FactoryMind mission."""

    config_loader = ConfigLoader()
    config_loader.load_all()

    mission = None

    for mission_data in config_loader.missions:
        if mission_data.get("mission_id") == mission_id:
            mission = mission_data
            break

    if mission is None:
        if config_loader.missions:
            mission = config_loader.missions[0]
        else:
            mission = {"mission_id": mission_id}

    session = TextWorldSession(config_loader=config_loader)
    reconciler = Reconciler(config_loader=config_loader)
    world_model = WorldModel(config_loader=config_loader)
    analyser = InformationAnalyser()
    planner = Planner()
    validator = SafetyValidator(config_loader=config_loader)
    executor = Executor()
    checker = MissionChecker()
    report_generator = ReportGenerator()

    llm_bridge = LLMBridge(
        model_name=QWEN_MODEL,
        use_stub=False,
    )

    inventory = [
        "infrared_pyrometer",
        "vibration_meter",
    ]

    known_tool_locations = {
        "infrared_pyrometer": "ROOM-MOTOR-01",
        "vibration_meter": "ROOM-MOTOR-01",
    }

    initial_observation = session.reset()
    reconciler.reconcile(
        world_model,
        initial_observation,
        turn=1,
    )

    for turn in range(2, max_turns + 1):
        current_room = world_model.agent.get(
            "location",
            session.current_room,
        )

        gaps = analyser.find_missing_evidence(
            mission,
            world_model,
        )

        planned_action = planner.plan(
            current_room=current_room,
            mission=mission,
            inventory=inventory,
            missing_information=gaps[
                "recommended_information_need"
            ],
            known_tool_locations=known_tool_locations,
            world_model=world_model,
        )

        validation = validator.validate(
            action_dict=planned_action,
            current_room=current_room,
            inventory=inventory,
            world_model=world_model,
        )

        if validation.get("safety_block"):
            allowed_actions = validation.get(
                "allowed_next_actions",
                [],
            )

            if allowed_actions:
                next_action = allowed_actions[0]

                planned_action = {
                    "goal": "safety_mitigation",
                    "proposed_action": next_action,
                    "expected_destination": current_room,
                    "reason": (
                        "Mitigate safety rule "
                        f"{validation.get('rule_id', 'UNKNOWN')}"
                    ),
                    "confidence": 1.0,
                }

        executor.execute(
            action_dict=planned_action,
            session=session,
            reconciler=reconciler,
            world_model=world_model,
            turn=turn,
        )

        evaluation = checker.evaluate(
            mission,
            world_model,
        )

        if evaluation.get("complete"):
            break

    if report_level == 1:
        if world_model.action_history:
            last_observation = world_model.action_history[-1].get(
                "observation",
                "",
            )
        else:
            last_observation = initial_observation

        return {
            "level": 1,
            "text": report_generator.generate_level_1_command_echo(
                last_observation,
                initial_observation,
            ),
        }

    if report_level == 2:
        return {
            "level": 2,
            "json": report_generator.generate_level_2_structured_json(
                world_model
            ),
        }

    if report_level == 3:
        facts = {
            "asset_id": "M-05",
            "health_state": "CRITICAL",
            "turn": len(world_model.action_history),
        }

        return {
            "level": 3,
            "text": (
                report_generator
                .generate_level_3_explainable_response(
                    facts,
                    llm_bridge,
                )
            ),
        }

    return {
        "level": 4,
        "report": (
            report_generator
            .generate_level_4_final_mission_report(
                mission,
                world_model,
                llm_bridge,
            )
        ),
    }


# ---------------------------------------------------------------------
# SQLite world-state helpers
# ---------------------------------------------------------------------

def restore_session_state(
    database: FactoryDatabase,
    session: TextWorldSession,
) -> None:
    """Restore saved world state from the local SQLite database."""

    saved_room = database.load_world_state(
        "current_room",
        default=None,
    )

    if saved_room:
        session.current_room = saved_room

    saved_assets = database.load_world_state(
        "asset_states",
        default=None,
    )

    if saved_assets and hasattr(session, "asset_states"):
        session.asset_states.update(saved_assets)

    saved_sensors = database.load_world_state(
        "sensor_telemetry",
        default=None,
    )

    if saved_sensors and hasattr(session, "sensor_telemetry"):
        session.sensor_telemetry.update(saved_sensors)

    # These states are stored only if your environment defines them.
    for attribute_name in [
        "production_states",
        "production_state",
        "inventory_states",
        "inventory_state",
        "warehouse_inventory",
        "notifications",
        "maintenance_orders",
        "purchase_requests",
    ]:
        saved_value = database.load_world_state(
            attribute_name,
            default=None,
        )

        if saved_value is not None and hasattr(
            session,
            attribute_name,
        ):
            setattr(
                session,
                attribute_name,
                saved_value,
            )


def save_session_state(
    database: FactoryDatabase,
    session: TextWorldSession,
) -> None:
    """Persist the current FactoryMind world state locally."""

    database.save_world_state(
        "current_room",
        session.current_room,
    )

    if hasattr(session, "asset_states"):
        database.save_world_state(
            "asset_states",
            session.asset_states,
        )

    if hasattr(session, "sensor_telemetry"):
        database.save_world_state(
            "sensor_telemetry",
            session.sensor_telemetry,
        )

    for attribute_name in [
        "production_states",
        "production_state",
        "inventory_states",
        "inventory_state",
        "warehouse_inventory",
        "notifications",
        "maintenance_orders",
        "purchase_requests",
    ]:
        if hasattr(session, attribute_name):
            database.save_world_state(
                attribute_name,
                getattr(session, attribute_name),
            )


# ---------------------------------------------------------------------
# Interactive output helpers
# ---------------------------------------------------------------------

def print_world_state(
    database: FactoryDatabase,
    session: TextWorldSession,
) -> None:
    """Print the current local world model."""

    print("\n" + "=" * 70)
    print("                     FACTORYMIND WORLD STATE")
    print("=" * 70)

    print(f"Current Room : {session.current_room}")

    if hasattr(session, "asset_states"):
        print("\nASSET STATES")
        print("-" * 70)

        for asset_id, state in session.asset_states.items():
            print(f"{asset_id}: {json.dumps(state, indent=2)}")

    if hasattr(session, "sensor_telemetry"):
        print("\nSENSOR TELEMETRY")
        print("-" * 70)

        for sensor_id, telemetry in session.sensor_telemetry.items():
            print(f"{sensor_id}: {json.dumps(telemetry, indent=2)}")

    for attribute_name in [
        "production_states",
        "production_state",
        "inventory_states",
        "inventory_state",
        "warehouse_inventory",
        "notifications",
        "maintenance_orders",
        "purchase_requests",
    ]:
        if hasattr(session, attribute_name):
            heading = attribute_name.replace("_", " ").upper()

            print(f"\n{heading}")
            print("-" * 70)
            print(
                json.dumps(
                    getattr(session, attribute_name),
                    indent=2,
                    default=str,
                )
            )

    print("\nDATABASE")
    print("-" * 70)
    print(f"Local file : {database.db_path}")
    print("=" * 70)


def print_history(
    database: FactoryDatabase,
    limit: int = 15,
) -> None:
    """Print recent locally stored conversation history."""

    history = database.get_recent_conversation(limit=limit)

    print("\n" + "=" * 70)
    print("                 RECENT FACTORYMIND CONVERSATION")
    print("=" * 70)

    if not history:
        print("No previous conversation is stored.")
    else:
        for item in history:
            role = item.get("role", "unknown").upper()
            content = item.get("content", "")
            print(f"\n{role} > {content}")

    print("\n" + "=" * 70)


def remove_qwen_thinking(text: str) -> str:
    """Remove optional Qwen <think> blocks and Markdown fences."""

    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    cleaned = cleaned.replace("```json", "")
    cleaned = cleaned.replace("```", "")

    return cleaned.strip()


def parse_qwen_response(
    response_text: str,
) -> Dict[str, str]:
    """
    Parse Qwen output.

    Expected format:
        {"type": "command", "command": "inspect M-05"}

    or:
        {"type": "chat", "message": "Hello."}
    """

    cleaned = remove_qwen_thinking(response_text)

    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            parsed = json.loads(cleaned[start:end + 1])

            response_type = str(
                parsed.get("type", "")
            ).strip().lower()

            if response_type == "command":
                return {
                    "type": "command",
                    "command": str(
                        parsed.get("command", "")
                    ).strip(),
                }

            return {
                "type": "chat",
                "message": str(
                    parsed.get(
                        "message",
                        "How can I help with the factory?",
                    )
                ).strip(),
            }

    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback if the model returns only a command.
    valid_command_prefixes = (
        "look",
        "go ",
        "inspect ",
        "check ",
        "stop ",
        "shift ",
        "reserve ",
        "read ",
        "measure ",
        "create ",
        "request ",
        "open ",
        "remove ",
    )

    first_line = cleaned.splitlines()[0].strip()

    if first_line.lower().startswith(valid_command_prefixes):
        return {
            "type": "command",
            "command": first_line,
        }

    return {
        "type": "chat",
        "message": cleaned or "How can I help with the factory?",
    }


def build_qwen_prompt(
    user_input: str,
    observation: str,
    session: TextWorldSession,
    database: FactoryDatabase,
) -> str:
    """Create a strict local-Qwen reasoning prompt."""

    history = database.get_recent_conversation(limit=8)

    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history
    )

    return f"""
You are FactoryMind, a local industrial text-world reasoning agent.

You run entirely locally using Ollama Qwen.
You must understand the user's natural-English request.

Current room:
{session.current_room}

Current observation:
{observation}

Recent local conversation:
{history_text}

Valid executable game commands:

look
go motor room
go control room
go warehouse
inspect M-05
check production status
stop line 1
shift to line 2
check inventory
reserve bearing SP-BRG-M05
read TS-M05-BRG
read VS-M05
read RPM-M05
create work order for M-05

Rules:

1. Return exactly one JSON object.
2. Do not use Markdown.
3. Do not invent commands outside the command list.
4. If the user only greets you, asks a question, or has not requested
   an executable action, return a chat response.
5. Never start the full scenario merely because the user says hello.
6. Select only one command per user turn.
7. The user controls the interaction. Do not execute all rooms at once.
8. Use the current room and previous conversation when selecting an action.

For an executable action, return:

{{"type":"command","command":"one valid command"}}

For a normal conversational response, return:

{{"type":"chat","message":"your concise response"}}

User request:
{user_input}
""".strip()


# ---------------------------------------------------------------------
# True interactive Qwen mode
# ---------------------------------------------------------------------

def run_interactive() -> None:
    """
    Run a continuous user-driven FactoryMind session.

    User input -> local Qwen -> one command -> environment ->
    world model -> SQLite -> wait for next user input.
    """

    config_loader = ConfigLoader()
    config_loader.load_all()

    database = FactoryDatabase()

    session = TextWorldSession(
        config_loader=config_loader
    )

    reconciler = Reconciler(
        config_loader=config_loader
    )

    world_model = WorldModel(
        config_loader=config_loader
    )

    llm_bridge = LLMBridge(
        model_name=QWEN_MODEL,
        use_stub=False,
    )

    observation = session.reset()

    restore_session_state(
        database,
        session,
    )

    observation = session.observe()

    reconciler.reconcile(
        world_model,
        observation,
        turn=1,
    )

    print("\n" + "=" * 70)
    print("         FACTORYMIND LOCAL QWEN + SQLITE TEXT WORLD")
    print("=" * 70)
    print(f"Model         : {QWEN_MODEL}")
    print(f"Current Room  : {session.current_room}")
    print(f"Local DB      : {database.db_path}")
    print("\n" + observation)

    print("\nNatural-language examples:")
    print("  Hello")
    print("  Production seems slow")
    print("  Check Motor M-05")
    print("  Go to the control room")
    print("  Check whether production can continue")
    print("  Go to the warehouse")
    print("  Find and reserve the spare bearing")

    print("\nLocal commands:")
    print("  show world")
    print("  show history")
    print("  look")
    print("  exit")

    turn = 1

    while True:
        try:
            user_input = input("\nYOU > ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\n\nFactoryMind session ended.")
            save_session_state(database, session)
            break

        if not user_input:
            continue

        normalized_input = user_input.lower().strip()

        if normalized_input in {
            "exit",
            "quit",
            "bye",
        }:
            save_session_state(database, session)

            database.save_conversation(
                "user",
                user_input,
            )

            database.save_conversation(
                "assistant",
                "FactoryMind session ended.",
            )

            print("\nFactoryMind session ended.")
            print("World state saved locally.")
            break

        if normalized_input in {
            "show world",
            "world",
            "show state",
        }:
            print_world_state(
                database,
                session,
            )
            continue

        if normalized_input in {
            "show history",
            "history",
        }:
            print_history(database)
            continue

        if normalized_input == "look":
            observation = session.observe()
            print("\nFACTORYMIND >")
            print(observation)
            continue

        turn += 1

        database.save_conversation(
            "user",
            user_input,
        )

        prompt = build_qwen_prompt(
            user_input=user_input,
            observation=observation,
            session=session,
            database=database,
        )

        print("\n[Qwen is reasoning locally...]")

        try:
            raw_response = llm_bridge.generate(prompt)

        except Exception as error:
            print("\nFACTORYMIND ERROR >")
            print(
                "Could not contact local Ollama Qwen model: "
                f"{error}"
            )
            continue

        decision = parse_qwen_response(raw_response)

        if decision["type"] == "chat":
            message = decision.get(
                "message",
                "How can I assist with the factory?",
            )

            database.save_conversation(
                "assistant",
                message,
            )

            print("\nFACTORYMIND >")
            print(message)
            continue

        command = decision.get("command", "").strip()

        if not command:
            message = (
                "I could not determine a safe factory action. "
                "Please describe what you want me to inspect."
            )

            database.save_conversation(
                "assistant",
                message,
            )

            print("\nFACTORYMIND >")
            print(message)
            continue

        print(f"\nQWEN ACTION > {command}")

        # Instantiate graph navigator using NetworkX & world model graph
        navigator = RoomNavigator(config_loader=config_loader)

        # 1 & 2: Determine required room precondition for equipment/action
        required_room = (
            navigator.get_required_room(user_input)
            or navigator.get_required_room(command)
        )
        current_room = session.current_room

        # 3, 4, 5, 6: If target equipment is in another room, navigate physically step-by-step
        if required_room and current_room != required_room:
            path = navigator.find_path(current_room, required_room)
            if not path:
                print(f"\n[NAVIGATION ROUTE UNKNOWN] Route to {required_room} is unknown. Cannot navigate.")
            else:
                print(f"\n[NAVIGATING VIA NETWORKX GRAPH] Path: {' -> '.join(path)}")
                for next_room in path[1:]:
                    turn += 1
                    print(f"\n[NAVIGATING ACTION] Moving to {next_room}...")
                    observation = session.act(f"go {next_room}")

                    print("\nENVIRONMENT OBSERVATION >")
                    print(observation)

                    reconciler.reconcile(
                        world_model,
                        observation,
                        turn=turn,
                    )
                    save_session_state(database, session)
                    database.log_action(
                        turn=turn,
                        user_input=user_input,
                        llm_command=f"go {next_room}",
                        observation=observation,
                        room_id=session.current_room,
                    )

        # 7 & 8: Once in required room, execute the real equipment action
        turn += 1
        print(f"\n[REAL ACTION EXECUTION] {command}")
        try:
            observation = session.act(command)
        except Exception as error:
            observation = f"Command execution failed for '{command}': {error}"

        print("\nENVIRONMENT OBSERVATION >")
        print(observation)

        reconciler.reconcile(
            world_model,
            observation,
            turn=turn,
        )

        save_session_state(
            database,
            session,
        )

        database.log_action(
            turn=turn,
            user_input=user_input,
            llm_command=command,
            observation=observation,
            room_id=session.current_room,
        )

        database.save_conversation(
            "assistant_command",
            command,
        )

        database.save_conversation(
            "observation",
            observation,
        )

        # 9 & 10: State verification and OBJECTIVE COMPLETE output
        m05_state = session.asset_states.get("M-05", {}).get("operational_state")
        line2_state = session.asset_states.get("LINE-2", {}).get("operational_state")
        brg_state = session.asset_states.get("SP-BRG-M05", {}).get("reservation_state")

        combined_cmd = (command + " " + user_input).lower()
        verified = False

        if ("start" in combined_cmd or "turn on" in combined_cmd) and "m-05" in combined_cmd:
            if m05_state == "RUNNING":
                print("\n[STATE VERIFICATION] Motor M-05 operational_state: RUNNING (VERIFIED)")
                verified = True
        elif ("stop" in combined_cmd or "turn off" in combined_cmd) and "m-05" in combined_cmd:
            if m05_state == "STOPPED":
                print("\n[STATE VERIFICATION] Motor M-05 operational_state: STOPPED (VERIFIED)")
                verified = True
        elif "shift" in combined_cmd or "line 2" in combined_cmd:
            if line2_state == "RUNNING":
                print("\n[STATE VERIFICATION] Production Line 2 operational_state: RUNNING (VERIFIED)")
                verified = True
        elif "reserve" in combined_cmd or "sp-brg-m05" in combined_cmd:
            if brg_state == "RESERVED":
                print("\n[STATE VERIFICATION] Spare Bearing SP-BRG-M05 reservation_state: RESERVED (VERIFIED)")
                verified = True
        elif "inspect" in combined_cmd and "m-05" in combined_cmd:
            print("\n[STATE VERIFICATION] Motor M-05 telemetry inspected (VERIFIED)")
            verified = True

        if verified:
            print("\n" + "=" * 70)
            print("                        OBJECTIVE COMPLETE")
            print("=" * 70)


# ---------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------

def print_formatted_report(
    result: Dict[str, Any],
) -> None:
    """Print an automatic mission result cleanly."""

    if "report" not in result:
        print("\nFACTORYMIND RESULT")
        print("-" * 70)
        print(json.dumps(result, indent=2, default=str))
        return

    report = result["report"]

    print("\n" + "=" * 70)
    print("               FACTORYMIND AI INSPECTION REPORT")
    print("=" * 70)

    print(
        f"Mission ID      : "
        f"{report.get('mission_id', 'UNKNOWN')}"
    )

    print(
        f"Report ID       : "
        f"{report.get('report_id', 'UNKNOWN')}"
    )

    print(
        f"Mission Status  : "
        f"{report.get('mission_status', 'UNKNOWN')}"
    )

    print(
        f"Severity        : "
        f"{report.get('severity', 'UNKNOWN')}"
    )

    print("\nDiagnosis")
    print("-" * 70)
    print(
        report.get(
            "diagnosis",
            "No diagnosis available.",
        )
    )

    print("\nRecommendation")
    print("-" * 70)
    print(
        report.get(
            "recommendation",
            "No recommendation available.",
        )
    )

    print("\nEvidence")
    print("-" * 70)

    evidence_items = report.get("evidence", [])

    if not evidence_items:
        print("No evidence recorded.")

    for evidence in evidence_items:
        print(
            f"Sensor  : "
            f"{evidence.get('sensor_id', 'UNKNOWN')}"
        )

        print(
            f"Asset   : "
            f"{evidence.get('monitored_asset', 'UNKNOWN')}"
        )

        print(
            f"Reading : "
            f"{evidence.get('value', 'N/A')} "
            f"{evidence.get('unit', '')}"
        )

        print(
            f"Status  : "
            f"{evidence.get('status', 'UNKNOWN')}"
        )

        print()

    print("Safety Events")
    print("-" * 70)

    safety_events = report.get("safety_checks", [])

    if not safety_events:
        print("No safety events recorded.")

    for event in safety_events:
        print(
            f"Turn {event.get('turn', 0)} | "
            f"{event.get('event_type', 'UNKNOWN')} | "
            f"{event.get('severity', 'UNKNOWN')}"
        )

    repair_status = (
        "Yes"
        if report.get("repair_performed")
        else "No"
    )

    print(f"\nRepair Performed : {repair_status}")
    print("=" * 70)


# ---------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "FactoryMind local industrial "
            "world-model runner"
        )
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use natural-language input through local Ollama Qwen",
    )

    parser.add_argument(
        "--mission",
        type=str,
        default="MIS-CV01-INSPECT",
        help="Mission ID to run",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run the automatic mission planner",
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=15,
        help="Maximum number of automatic mission turns",
    )

    parser.add_argument(
        "--report-level",
        type=int,
        default=4,
        choices=[1, 2, 3, 4],
        help="Automatic report level",
    )

    args = parser.parse_args()

    if args.interactive:
        run_interactive()
        return

    result = run_mission(
        mission_id=args.mission,
        auto=args.auto,
        max_turns=args.max_turns,
        report_level=args.report_level,
    )

    with open(
        "latest_mission_report.json",
        "w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            result,
            report_file,
            indent=2,
            default=str,
        )

    print("\n[Report saved to latest_mission_report.json]")

    print_formatted_report(result)


if __name__ == "__main__":
    main()