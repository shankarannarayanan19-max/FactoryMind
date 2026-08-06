"""Reconciliation module for FactoryMind persistent world model."""

from typing import Dict, Any, Optional
from factorymind.config_loader import ConfigLoader
from factorymind.parser import TextParser
from factorymind.extractor import FactExtractor
from factorymind.event_engine import EventEngine
from factorymind.world_model import WorldModel

class Reconciler:
    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        parser: Optional[TextParser] = None,
        extractor: Optional[FactExtractor] = None,
        event_engine: Optional[EventEngine] = None
    ):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader
        self.parser = parser or TextParser(config_loader=self.config_loader)
        self.extractor = extractor or FactExtractor(config_loader=self.config_loader)
        self.event_engine = event_engine or EventEngine()

    def reconcile(
        self,
        world_model: WorldModel,
        observation: str,
        nav_intent: Optional[Dict[str, str]] = None,
        turn: int = 0
    ) -> Dict[str, Any]:
        """Parse observation, update WorldModel persistent state according to §10 rules, and emit domain events."""
        # 1. Parse observation
        prev_room = world_model.agent.get("location") if world_model.agent else "UNKNOWN"
        parse_res = self.parser.parse_observation(observation, nav_intent=nav_intent, prev_room=prev_room)

        # 2. Handle transition conflict event
        if parse_res.get("transition_conflict"):
            evt_tc = self.event_engine.emit(
                event_type="LOCATION_TRANSITION_CONFLICT",
                payload=parse_res["transition_conflict"],
                severity=parse_res["transition_conflict"].get("severity", "WARNING"),
                turn=turn
            )
            world_model.events.append(evt_tc)
        # 3. Update agent location (Rule 1: refresh turn & confidence)
        room_info = parse_res["room_info"]
        prev_loc = world_model.agent.get("location") if world_model.agent else "UNKNOWN"
        world_model.update_agent_location(
            room_id=room_info["room"],
            confidence=room_info["confidence"],
            source=room_info["source"],
            turn=turn
        )
        if prev_loc != room_info["room"]:
            evt_re = self.event_engine.emit(
                event_type="ROOM_ENTERED",
                payload={"room": room_info["room"], "previous_room": prev_loc},
                severity="INFO",
                turn=turn
            )
            world_model.events.append(evt_re)

        parsed_facts = parse_res["parsed_facts"]

        # 4. Extract entities with alias resolution (§2 Step 2)
        entities = self.extractor.extract_entities(parsed_facts)
        for aid in entities["assets"]:
            if aid in world_model.assets and world_model.assets[aid].get("last_observed_turn", 0) == 0:
                evt_ad = self.event_engine.emit(
                    event_type="ASSET_DISCOVERED",
                    payload={"asset_id": aid, "room": room_info["room"]},
                    severity="INFO",
                    turn=turn
                )
                world_model.events.append(evt_ad)

        # 5. Handle unresolved entities
        for unresolved_id in entities["unresolved"]:
            evt_u = self.event_engine.emit(
                event_type="UNRESOLVED_ENTITY",
                payload={
                    "entity_id": unresolved_id,
                    "description": f"Unrecognized entity ID '{unresolved_id}' found in observation."
                },
                severity="WARNING",
                turn=turn
            )
            world_model.events.append(evt_u)

        # 6. Extract static relationships (Rule 1 & Rule 3: persist & refresh)
        relationships = self.extractor.extract_relationships(parsed_facts)
        for rel in relationships:
            world_model.add_relationship_rule1_3(
                source=rel["source"],
                relation=rel["relation"],
                target=rel["target"],
                turn=turn
            )

        # 7. Extract measurements & evaluate Rule 4 contradiction handling
        measurements = self.extractor.extract_measurements(parsed_facts)
        for m in measurements:
            raw_ev = m.get("raw_evidence", "").lower()
            monitored_asset = world_model.resolve_asset_id(m["monitored_asset"])

            # Detect if measurement comes from a portable tool (Rule 4)
            tool_name = None
            if "pyrometer" in raw_ev or "infrared_pyrometer" in raw_ev:
                tool_name = "infrared_pyrometer"
            elif "vibration_meter" in raw_ev or "vib_meter" in raw_ev or "meter" in raw_ev:
                tool_name = "vibration_meter"

            if tool_name and monitored_asset:
                fixed_sensor_id = None
                fixed_val = None
                for sid, sdata in world_model.sensors.items():
                    if sdata.get("monitored_asset") == monitored_asset and sdata.get("unit") == m["unit"]:
                        fixed_sensor_id = sid
                        fixed_val = sdata.get("latest_value")
                        break

                if fixed_sensor_id and fixed_val is not None and abs(fixed_val - m["value"]) > 10.0:
                    # Rule 4: Contradiction detected! Set SENSOR_VALIDATION_REQUIRED and create CONTRADICTS relation (NEVER average!)
                    world_model.add_contradiction_rule4(
                        fixed_sensor_id=fixed_sensor_id,
                        portable_tool_id=tool_name,
                        fixed_val=fixed_val,
                        portable_val=m["value"],
                        target_asset=monitored_asset,
                        turn=turn
                    )
                    evt_c = self.event_engine.emit(
                        event_type="SENSOR_CONTRADICTION",
                        payload={
                            "fixed_sensor_id": fixed_sensor_id,
                            "portable_tool_id": tool_name,
                            "fixed_value": fixed_val,
                            "portable_value": m["value"],
                            "monitored_asset": monitored_asset,
                            "status": "SENSOR_VALIDATION_REQUIRED"
                        },
                        severity="WARNING",
                        turn=turn
                    )
                    world_model.events.append(evt_c)
                    continue

            sensor_id = world_model.resolve_asset_id(m["sensor_id"] or f"UNKNOWN_SENSOR_{m['monitored_asset']}")

            # Update normal sensor reading
            world_model.update_sensor_reading(
                sensor_id=sensor_id,
                value=m["value"],
                unit=m["unit"],
                status=m["status"],
                monitored_asset=monitored_asset,
                turn=turn
            )
            
            evt_m = self.event_engine.emit(
                event_type="MEASUREMENT_RECORDED",
                payload=m,
                severity="INFO",
                turn=turn
            )
            world_model.events.append(evt_m)

            if m["status"] in ("WARNING", "CRITICAL"):
                evt_b = self.event_engine.emit(
                    event_type="THRESHOLD_BREACH",
                    payload=m,
                    severity=m["status"],
                    turn=turn
                )
                world_model.events.append(evt_b)

                evt_alarm = self.event_engine.emit(
                    event_type="ALARM_OBSERVED",
                    payload={"sensor_id": sensor_id, "monitored_asset": monitored_asset, "status": m["status"], "value": m["value"]},
                    severity=m["status"],
                    turn=turn
                )
                world_model.events.append(evt_alarm)

                # Evaluate asset health degradation (Rule 2)
                if monitored_asset:
                    update_res = world_model.update_asset_state_rule2(
                        asset_id=monitored_asset,
                        state_key="health_state",
                        value=m["status"],
                        turn=turn
                    )
                    if update_res["degraded"]:
                        evt_d = self.event_engine.emit(
                            event_type="ASSET_HEALTH_DEGRADED",
                            payload={
                                "asset_id": monitored_asset,
                                "old_health_state": update_res["old_value"],
                                "new_health_state": update_res["new_value"],
                                "turn": turn
                            },
                            severity=m["status"],
                            turn=turn
                        )
                        world_model.events.append(evt_d)

        # 8. Extract states (Rule 2: dynamic state replacement & history preservation)
        states = self.extractor.extract_states(parsed_facts)
        updated_states_count = 0
        for st in states:
            entity_id = world_model.resolve_asset_id(st["entity_id"])
            state_key = st["state_key"]
            val = st["value"]

            update_res = world_model.update_asset_state_rule2(
                asset_id=entity_id,
                state_key=state_key,
                value=val,
                turn=turn
            )
            if update_res["state_changed"]:
                updated_states_count += 1
                evt_s = self.event_engine.emit(
                    event_type="STATE_CHANGED",
                    payload={
                        "entity_id": entity_id,
                        "state_key": state_key,
                        "value": val,
                        "raw_evidence": st["raw_evidence"]
                    },
                    severity="INFO",
                    turn=turn
                )
                world_model.events.append(evt_s)

                if val == "STOPPED" and ("request shutdown" in observation.lower() or "shutdown request" in observation.lower()):
                    evt_shut = self.event_engine.emit(
                        event_type="SHUTDOWN_REQUESTED",
                        payload={"asset_id": entity_id, "turn": turn},
                        severity="WARNING",
                        turn=turn
                    )
                    world_model.events.append(evt_shut)

                if update_res["degraded"]:
                    evt_d = self.event_engine.emit(
                        event_type="ASSET_HEALTH_DEGRADED",
                        payload={
                            "asset_id": entity_id,
                            "old_health_state": update_res["old_value"],
                            "new_health_state": update_res["new_value"],
                            "turn": turn
                        },
                        severity=val if val in ("WARNING", "CRITICAL") else "WARNING",
                        turn=turn
                    )
                    world_model.events.append(evt_d)

        # 9. Record action log & compress events if needed
        action_entry = {
            "turn": turn,
            "observation": observation,
            "nav_intent": nav_intent,
            "room": room_info["room"]
        }
        world_model.action_history.append(action_entry)
        world_model.compress_events(max_events=100)

        # 10. Emit world model updated event
        evt_wm = self.event_engine.emit(
            event_type="WORLD_MODEL_UPDATED",
            payload={
                "room": room_info["room"],
                "assets_count": len(world_model.assets),
                "sensors_count": len(world_model.sensors),
                "turn": turn
            },
            severity="INFO",
            turn=turn
        )
        world_model.events.append(evt_wm)

        return {
            "room": room_info["room"],
            "entities": entities,
            "relationships_count": len(world_model.relationships),
            "measurements_count": len(measurements),
            "states_updated": updated_states_count
        }



