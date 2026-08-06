"""TextWorld Environment Interface for FactoryMind.

Authors factory world via TextWorld GameMaker and wraps interactive session
exposing reset(), act(command) -> observation, and observe().
"""

import os
from typing import Dict, Any, Optional, List
import textworld
from textworld.generator import GameMaker
from factorymind.config_loader import ConfigLoader

class TextWorldFactoryWorld:
    """Creates a TextWorld game structure using GameMaker based on loaded configs."""
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader
        self.maker = GameMaker()

    def build_game(self) -> GameMaker:
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        assets_cfg = self.asset_registry = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.sensor_registry = self.config_loader.sensor_registry.get("sensors", {})

        room_nodes = {}
        for room_id, rdata in rooms_cfg.items():
            r_desc = rdata.get("description", "")
            room_node = self.maker.new_room(room_id)
            room_node.description = r_desc
            room_nodes[room_id] = room_node

        # Connect rooms based on exits
        opposite_dir = {"east": "west", "west": "east", "north": "south", "south": "north"}
        for room_id, rdata in rooms_cfg.items():
            exits = rdata.get("exits", {})
            for dir_name, dest_id in exits.items():
                if dest_id in room_nodes and dir_name in opposite_dir:
                    opp_dir = opposite_dir[dir_name]
                    r1_exit = getattr(room_nodes[room_id], dir_name)
                    r2_exit = getattr(room_nodes[dest_id], opp_dir)
                    try:
                        self.maker.connect(r1_exit, r2_exit)
                    except Exception:
                        pass

        # Set player start
        if "ROOM-PACK-01" in room_nodes:
            self.maker.set_player(room_nodes["ROOM-PACK-01"])

        # Add assets as entity objects
        for asset_id, adata in assets_cfg.items():
            room_id = adata.get("room")
            obj = self.maker.new(type="o", name=asset_id)
            if room_id in room_nodes:
                room_nodes[room_id].add(obj)

        # Add sensors as entity objects
        for sensor_id, sdata in sensors_cfg.items():
            room_id = sdata.get("room")
            obj = self.maker.new(type="o", name=sensor_id)
            if room_id in room_nodes:
                room_nodes[room_id].add(obj)

        return self.maker


class TextWorldSession:
    """Interactive session managing world state and observation formatting for FactoryMind."""
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader
        self.builder = TextWorldFactoryWorld(self.config_loader)
        self.maker = self.builder.build_game()
        
        # State tracking
        self.current_room = "ROOM-PACK-01"
        self.turn_count = 0
        self.inventory = ["infrared_pyrometer", "vibration_meter"]

        # Dynamic world state
        self.asset_states = {
            "CV-01": {"operational_state": "RUNNING", "energy_state": "ENERGIZED"},
            "CV-M01": {"operational_state": "RUNNING", "energy_state": "ENERGIZED"},
            "CV-M02": {"operational_state": "RUNNING", "energy_state": "ENERGIZED"},
            "GUARD-CV01": {"access_state": "CLOSED", "safety_state": "ENGAGED"},
            "PCS-CV01": {"operational_state": "NORMAL", "energy_state": "ENERGIZED"},
        }

        # Dynamic sensor telemetry
        self.sensor_telemetry = {
            "TS-CVM02-BRG": {"value": 82.0, "unit": "C", "status": "WARNING", "alarm": "ELEVATED_TEMPERATURE"},
            "VS-CVM02": {"value": 5.8, "unit": "mm/s", "status": "CRITICAL", "alarm": "SEVERE_VIBRATION"},
        }

        self.last_observation = ""
        self.reset()

    def reset(self) -> str:
        self.turn_count = 0
        self.current_room = "ROOM-PACK-01"
        self.last_observation = self.observe()
        return self.last_observation

    def observe(self) -> str:
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        room_data = rooms_cfg.get(self.current_room, {})
        rname = room_data.get("name", self.current_room)
        exits = room_data.get("exits", {})

        exits_str_parts = [f"{direction} to {rooms_cfg.get(dest, {}).get('name', dest)} ({dest})" for direction, dest in exits.items()]
        exits_str = ", ".join(exits_str_parts) if exits_str_parts else "none"

        # Find assets and sensors in current room
        assets_in_room = [aid for aid, adata in self.config_loader.asset_registry.get("assets", {}).items() if adata.get("room") == self.current_room]
        sensors_in_room = [sid for sid, sdata in self.config_loader.sensor_registry.get("sensors", {}).items() if sdata.get("room") == self.current_room]

        equipment_desc_parts = []
        for aid in assets_in_room:
            aname = self.config_loader.asset_registry["assets"][aid]["name"]
            equipment_desc_parts.append(f"{aname} ({aid})")
        for sid in sensors_in_room:
            sname = self.config_loader.sensor_registry["sensors"][sid]["name"]
            equipment_desc_parts.append(f"{sname} ({sid})")

        equip_str = ", ".join(equipment_desc_parts)

        obs = (
            f"Location: {rname} ({self.current_room}).\n"
            f"Exits: {exits_str}.\n"
            f"You observe the following equipment: {equip_str}."
        )
        self.last_observation = obs
        return obs

    def act(self, command: str) -> str:
        self.turn_count += 1
        cmd = command.strip().lower()

        # Handle navigation
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        current_exits = rooms_cfg.get(self.current_room, {}).get("exits", {})

        if cmd in ["look", "l"]:
            return self.observe()

        if cmd.startswith("go ") or cmd in ["east", "west", "north", "south"]:
            direction = cmd.replace("go ", "").strip()
            if direction in current_exits:
                self.current_room = current_exits[direction]
                return self.observe()
            return f"You cannot go {direction} from here."

        # Handle 'inspect X'
        if cmd.startswith("inspect "):
            target_id = cmd.replace("inspect ", "").strip().upper()
            return self._handle_inspect(target_id)

        # Handle 'read X'
        if cmd.startswith("read "):
            target_id = cmd.replace("read ", "").strip().upper()
            return self._handle_read(target_id)

        # Handle 'check X'
        if cmd.startswith("check "):
            target_id = cmd.replace("check ", "").strip().upper()
            return self._handle_check(target_id)

        # Handle 'request shutdown of X'
        if "request shutdown of" in cmd:
            target_id = cmd.split("request shutdown of")[-1].strip().upper()
            return self._handle_shutdown(target_id)

        # Handle 'remove GUARD-X' or 'open GUARD-X'
        if "remove " in cmd or "open " in cmd:
            target_id = cmd.replace("remove ", "").replace("open ", "").strip().upper()
            return self._handle_remove_guard(target_id)

        # Handle 'measure <thing> of <asset> with <tool>'
        if cmd.startswith("measure "):
            return self._handle_measure(cmd)

        # Handle 'create work order for X'
        if "create work order for" in cmd:
            target_id = cmd.split("create work order for")[-1].strip().upper()
            return f"Work order WO-{target_id}-001 successfully created for asset {target_id}."

        return f"Command not recognized: '{command}'."

    def _handle_inspect(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        if target_id not in assets_cfg:
            return f"Asset {target_id} not found in {self.current_room}."

        adata = assets_cfg[target_id]
        aname = adata["name"]
        room_id = adata["room"]
        rname = self.config_loader.factory_map["rooms"].get(room_id, {}).get("name", room_id)
        state = self.asset_states.get(target_id, {"operational_state": "UNKNOWN", "energy_state": "UNKNOWN"})

        op_state = state.get("operational_state", "RUNNING")
        en_state = state.get("energy_state", "ENERGIZED")

        if target_id == "CV-01":
            return (
                f"Conveyor Line 1 (CV-01) is located in {rname} ({room_id}). "
                f"It consists of Main Drive Motor (CV-M01) and Tail Drive Motor & Bearing Assembly (CV-M02). "
                f"Protective Guard (GUARD-CV01) covers the tail drive assembly. "
                f"Operational state is {op_state}. Energy state is {en_state}."
            )
        elif target_id == "CV-M02":
            return (
                f"Tail Drive Motor & Bearing Assembly (CV-M02) is part of Conveyor Line 1 (CV-01) in {rname} ({room_id}). "
                f"It is monitored by Temperature Sensor (TS-CVM02-BRG) and Vibration Sensor (VS-CVM02). "
                f"Operational state is {op_state}. Energy state is {en_state}."
            )
        elif target_id == "CV-M01":
            return (
                f"Main Drive Motor (CV-M01) is part of Conveyor Line 1 (CV-01) in {rname} ({room_id}). "
                f"Operational state is {op_state}. Energy state is {en_state}."
            )
        elif target_id == "GUARD-CV01":
            acc_state = self.asset_states.get("GUARD-CV01", {}).get("access_state", "CLOSED")
            return (
                f"Conveyor Interlocked Guard (GUARD-CV01) protects tail drive assembly CV-M02 in {rname} ({room_id}). "
                f"Access state is {acc_state}."
            )
        else:
            return f"{aname} ({target_id}) located in {rname} ({room_id}). Operational state is {op_state}. Energy state is {en_state}."

    def _handle_read(self, target_id: str) -> str:
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})
        if target_id not in sensors_cfg:
            return f"Sensor {target_id} not found."

        sdata = sensors_cfg[target_id]
        sname = sdata["name"]
        monitors = sdata["monitors"]
        monitors_name = self.config_loader.asset_registry["assets"].get(monitors, {}).get("name", monitors)
        room_id = sdata["room"]
        rname = self.config_loader.factory_map["rooms"].get(room_id, {}).get("name", room_id)

        tdata = self.sensor_telemetry.get(target_id, {"value": 0.0, "unit": "N/A", "status": "NORMAL", "alarm": "NONE"})
        val = tdata["value"]
        unit = tdata["unit"]
        status = tdata["status"]
        alarm = tdata["alarm"]

        thresholds = self.config_loader.thresholds["thresholds"].get(monitors, {})
        param = "temperature_C" if "temperature" in sdata.get("sensor_type", "").lower() else "vibration_mm_s"
        thresh_info = thresholds.get(param, {"normal_max": 70.0, "warning_max": 80.0, "critical_above": 80.0})

        norm_m = thresh_info.get("normal_max")
        warn_m = thresh_info.get("warning_max")
        crit_m = thresh_info.get("critical_above")

        return (
            f"{sname} ({target_id}) monitors {monitors_name} ({monitors}) in {rname} ({room_id}). "
            f"Reading: {val} {unit}. Threshold normal max: {norm_m} {unit}, warning max: {warn_m} {unit}, critical above: {crit_m} {unit}. "
            f"Telemetry status: {status} (ALARM: {alarm})."
        )

    def _handle_check(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        if target_id not in assets_cfg:
            return f"Cabinet or asset {target_id} not found."

        adata = assets_cfg[target_id]
        aname = adata["name"]
        controls = adata.get("controls", "CV-01")
        controls_name = assets_cfg.get(controls, {}).get("name", controls)
        room_id = adata["room"]
        rname = self.config_loader.factory_map["rooms"].get(room_id, {}).get("name", room_id)

        controlled_state = self.asset_states.get(controls, {"operational_state": "RUNNING", "energy_state": "ENERGIZED"})
        en_state = controlled_state.get("energy_state", "ENERGIZED")
        op_state = controlled_state.get("operational_state", "RUNNING")

        return (
            f"{aname} ({target_id}) controls {controls_name} ({controls}) in {rname} ({room_id}). "
            f"Status panel confirms {controls} energy state is {en_state} and operational state is {op_state}."
        )

    def _handle_shutdown(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        if target_id not in assets_cfg:
            return f"Cannot shutdown unknown asset {target_id}."

        aname = assets_cfg[target_id]["name"]
        plc_id = "PCS-CV01"
        plc_name = assets_cfg.get(plc_id, {}).get("name", plc_id)

        # Update energy and operational state of CV-01 and child motors
        self.asset_states["CV-01"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["CV-M01"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["CV-M02"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}

        return (
            f"Shutdown request for {aname} ({target_id}) processed by {plc_name} ({plc_id}). "
            f"Motor drive de-energized. Operational state updated to STOPPED. Energy state updated to DE_ENERGIZED."
        )

    def _handle_remove_guard(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        if target_id not in assets_cfg:
            return f"Guard {target_id} not found."

        aname = assets_cfg[target_id]["name"]
        protects = assets_cfg[target_id].get("protects", "CV-01")
        protects_name = assets_cfg.get(protects, {}).get("name", protects)

        self.asset_states[target_id] = {"access_state": "OPEN", "safety_state": "DISENGAGED"}

        return (
            f"Interlocked Safety Guard ({target_id}) protecting {protects_name} ({protects}) tail drive assembly CV-M02 "
            f"has been opened and removed. Access state is now OPEN."
        )

    def _handle_measure(self, command_str: str) -> str:
        # e.g., "measure temperature of CV-M02 with infrared_pyrometer"
        parts = command_str.split()
        target_asset = "CV-M02"
        for part in parts:
            if part.upper() in self.config_loader.asset_registry.get("assets", {}):
                target_asset = part.upper()

        if "infrared_pyrometer" in command_str:
            return (
                f"Independent portable measurement taken for {target_asset} using infrared_pyrometer. "
                f"Surface temperature reading: 48.0 C (CALIBRATED)."
            )
        elif "vibration_meter" in command_str:
            return (
                f"Independent portable measurement taken for {target_asset} using vibration_meter. "
                f"Vibration velocity reading: 5.7 mm/s (CALIBRATED)."
            )

        return f"Measured {target_asset} with tool. Reading recorded."
