"""TextWorld Environment Interface for FactoryMind.

Authors factory world via TextWorld GameMaker and wraps interactive session
exposing reset(), act(command) -> observation, and observe().
"""

import os
from typing import Dict, Any, Optional, List
try:
    # pyrefly: ignore [missing-import]
    import textworld
    # pyrefly: ignore [missing-import]
    from textworld.generator import GameMaker
    TEXTWORLD_AVAILABLE = True
except ImportError:
    textworld = None
    GameMaker = None
    TEXTWORLD_AVAILABLE = False

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
        start_room = "ROOM-PACK-01" if "ROOM-PACK-01" in room_nodes else "ROOM-MOTOR-01"
        if start_room in room_nodes:
            self.maker.set_player(room_nodes[start_room])

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
        if TEXTWORLD_AVAILABLE:
            self.builder = TextWorldFactoryWorld(self.config_loader)
            self.maker = self.builder.build_game()
        else:
            self.builder = None
            self.maker = None
        # State tracking
        self.current_room = "ROOM-PACK-01"
        self.turn_count = 0
        self.inventory = ["infrared_pyrometer", "vibration_meter"]

        # Dynamic world state for 3-room scenario
        self.asset_states = {
            "M-05": {"operational_state": "RUNNING", "energy_state": "ENERGIZED", "health_state": "CRITICAL"},
            "LINE-1": {"operational_state": "RUNNING", "energy_state": "ENERGIZED", "line_status": "DEGRADED_HIGH_LOAD"},
            "LINE-2": {"operational_state": "IDLE", "energy_state": "STANDBY", "line_status": "AVAILABLE"},
            "PCS-LINE1": {"operational_state": "NORMAL", "energy_state": "ENERGIZED"},
            "PCS-LINE2": {"operational_state": "NORMAL", "energy_state": "ENERGIZED"},
            "INV-WH-01": {"operational_state": "ONLINE", "status": "AVAILABLE"},
            "SP-BRG-M05": {"reservation_state": "AVAILABLE", "item_count": 1},
            # Legacy assets fallback
            "CV-01": {"operational_state": "RUNNING", "energy_state": "ENERGIZED"},
            "CV-M01": {"operational_state": "RUNNING", "energy_state": "ENERGIZED"},
            "CV-M02": {"operational_state": "RUNNING", "energy_state": "ENERGIZED"},
            "GUARD-CV01": {"access_state": "CLOSED", "safety_state": "ENGAGED"},
            "PCS-CV01": {"operational_state": "NORMAL", "energy_state": "ENERGIZED"},
        }

        # Dynamic sensor telemetry
        self.sensor_telemetry = {
            "TS-M05-BRG": {"value": 88.0, "unit": "C", "status": "CRITICAL", "alarm": "HIGH_BEARING_TEMPERATURE"},
            "VS-M05": {"value": 6.2, "unit": "mm/s", "status": "CRITICAL", "alarm": "HIGH_VIBRATION_VELOCITY"},
            "RPM-M05": {"value": 950.0, "unit": "RPM", "status": "CRITICAL", "alarm": "REDUCED_ROTATIONAL_SPEED"},
            # Legacy sensor fallback
            "TS-CVM02-BRG": {"value": 82.0, "unit": "C", "status": "WARNING", "alarm": "ELEVATED_TEMPERATURE"},
            "VS-CVM02": {"value": 5.8, "unit": "mm/s", "status": "CRITICAL", "alarm": "SEVERE_VIBRATION"},
        }

        self.last_observation = ""
        self.reset()

    def reset(self) -> str:
        self.turn_count = 0
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        if "ROOM-PACK-01" in rooms_cfg:
            self.current_room = "ROOM-PACK-01"
        else:
            self.current_room = "ROOM-MOTOR-01"
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

        # Room Alias Resolution for physical movement
        room_name_map = {
            "motor room": "ROOM-MOTOR-01",
            "control room": "ROOM-CTRL-01",
            "warehouse": "ROOM-WH-01",
            "packaging bay 1": "ROOM-PACK-01"
        }

        # Room movement commands (e.g. "go motor room", "go control room", "go warehouse")
        for rname, rid in room_name_map.items():
            if cmd in [f"go {rname}", f"go to {rname}", f"enter {rname}", rname]:
                self.current_room = rid
                return self.observe()

        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        current_exits = rooms_cfg.get(self.current_room, {}).get("exits", {})

        if cmd in ["look", "l"]:
            return self.observe()

        if cmd.startswith("go ") or cmd in ["east", "west", "north", "south"]:
            target_str = cmd.replace("go ", "").strip()
            # If target_str is direct room ID
            if target_str.upper() in rooms_cfg:
                self.current_room = target_str.upper()
                return self.observe()
            if target_str in current_exits:
                self.current_room = current_exits[target_str]
                return self.observe()

        # Handle 'inspect M-05' or motor room diagnostics
        if "inspect m-05" in cmd or "check m-05" in cmd or ("inspect" in cmd and "m-05" in cmd):
            return self._handle_inspect_m05()

        # Handle 'check production status' or Control Room inspection
        if "production status" in cmd or "check line" in cmd or "running orders" in cmd:
            return self._handle_check_production_status()

        # Handle 'stop line 1' or 'shift to line 2'
        if "stop line 1" in cmd or "shutdown line 1" in cmd:
            return self._handle_stop_line_1()

        if "shift to line 2" in cmd or "transfer to line 2" in cmd or "shift production" in cmd:
            return self._handle_shift_to_line_2()

        # Handle 'check inventory' or Warehouse inspection
        if "inventory" in cmd or "spare" in cmd or "check warehouse" in cmd:
            return self._handle_check_inventory()

        # Handle 'reserve bearing' or 'reserve SP-BRG-M05'
        if "reserve" in cmd or "sp-brg-m05" in cmd:
            return self._handle_reserve_bearing()

        # Legacy command fallbacks
        if cmd.startswith("inspect "):
            target_id = cmd.replace("inspect ", "").strip().upper()
            return self._handle_inspect(target_id)

        if cmd.startswith("read "):
            target_id = cmd.replace("read ", "").strip().upper()
            return self._handle_read(target_id)

        if cmd.startswith("check "):
            target_id = cmd.replace("check ", "").strip().upper()
            return self._handle_check(target_id)

        if "request shutdown of" in cmd:
            target_id = cmd.split("request shutdown of")[-1].strip().upper()
            return self._handle_shutdown(target_id)

        if "remove " in cmd or "open " in cmd:
            target_id = cmd.replace("remove ", "").replace("open ", "").strip().upper()
            return self._handle_remove_guard(target_id)

        if cmd.startswith("measure "):
            return self._handle_measure(cmd)

        return f"Executed command: '{command}' in {self.current_room}."

    def _handle_inspect_m05(self) -> str:
        ts = self.sensor_telemetry["TS-M05-BRG"]
        vs = self.sensor_telemetry["VS-M05"]
        rpm = self.sensor_telemetry["RPM-M05"]
        return (
            f"Motor Room Inspection (ROOM-MOTOR-01): Drive Motor M-05 telemetry detected. "
            f"Bearing Temperature: {ts['value']} {ts['unit']} (CRITICAL - Exceeds 70.0 C limit). "
            f"Vibration Velocity: {vs['value']} {vs['unit']} (CRITICAL - Exceeds 4.5 mm/s limit). "
            f"Rotational Speed: {rpm['value']} {rpm['unit']} (CRITICAL - Reduced from 1480 RPM nominal). "
            f"Diagnosis: Severe bearing failure detected on Motor M-05."
        )

    def _handle_check_production_status(self) -> str:
        return (
            f"Control Room Inspection (ROOM-CTRL-01): SCADA Monitoring Station SCADA-MON-01 active. "
            f"Line 1 (LINE-1) status: DEGRADED due to M-05 bearing failure. "
            f"Line 2 (LINE-2) status: AVAILABLE (Idle backup line). "
            f"Active Running Order: ORD-101 (High-Priority Manufacturing Batch). "
            f"Recommended Decision: Stop Line 1, shift production to Line 2, and notify supervisor."
        )

    def _handle_stop_line_1(self) -> str:
        self.asset_states["LINE-1"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["M-05"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        return "Production Line 1 (LINE-1) successfully STOPPED via PLC Panel PCS-LINE1. Motor M-05 de-energized."

    def _handle_shift_to_line_2(self) -> str:
        self.asset_states["LINE-1"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["LINE-2"] = {"operational_state": "RUNNING", "energy_state": "ENERGIZED"}
        return (
            "Production successfully SHIFTED to Line 2 (LINE-2). Line 2 status updated to RUNNING. "
            "Supervisor notification dispatched via SCADA control interface."
        )

    def _handle_check_inventory(self) -> str:
        item = self.asset_states.get("SP-BRG-M05", {})
        count = item.get("item_count", 1)
        res_state = item.get("reservation_state", "AVAILABLE")
        return (
            f"Warehouse Inspection (ROOM-WH-01): Inventory Cabinet INV-WH-01 scanned. "
            f"Spare Part: Spare Motor M-05 Roller Bearing (SP-BRG-M05). "
            f"Availability: {count} unit(s) in stock. Reservation status: {res_state}."
        )

    def _handle_reserve_bearing(self) -> str:
        self.asset_states["SP-BRG-M05"] = {"reservation_state": "RESERVED", "item_count": 1}
        return (
            "Spare Bearing SP-BRG-M05 successfully RESERVED for Motor M-05 replacement. "
            "Maintenance work order WO-M05-REPAIR generated in Warehouse inventory system."
        )

    def _handle_inspect(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        if target_id not in assets_cfg:
            return f"Asset {target_id} not found in {self.current_room}."

        adata = assets_cfg[target_id]
        aname = adata["name"]
        room_id = adata.get("room", self.current_room)
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

        return f"{aname} ({target_id}) located in {rname} ({room_id}). Operational state is {op_state}. Energy state is {en_state}."

    def _handle_read(self, target_id: str) -> str:
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})
        if target_id not in sensors_cfg:
            return f"Sensor {target_id} not found."

        sdata = sensors_cfg[target_id]
        sname = sdata["name"]
        monitors = sdata["monitors"]
        monitors_name = self.config_loader.asset_registry.get("assets", {}).get(monitors, {}).get("name", monitors)
        room_id = sdata.get("room", self.current_room)
        rname = self.config_loader.factory_map.get("rooms", {}).get(room_id, {}).get("name", room_id)

        tdata = self.sensor_telemetry.get(target_id, {"value": 0.0, "unit": "N/A", "status": "NORMAL", "alarm": "NONE"})
        val = tdata["value"]
        unit = tdata["unit"]
        status = tdata["status"]
        alarm = tdata["alarm"]

        thresholds = self.config_loader.thresholds.get("thresholds", {}).get(monitors, {})
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
        room_id = adata.get("room", self.current_room)
        rname = self.config_loader.factory_map.get("rooms", {}).get(room_id, {}).get("name", room_id)

        controlled_state = self.asset_states.get(controls, {"operational_state": "RUNNING", "energy_state": "ENERGIZED"})
        en_state = controlled_state.get("energy_state", "ENERGIZED")
        op_state = controlled_state.get("operational_state", "RUNNING")

        return (
            f"{aname} ({target_id}) controls {controls_name} ({controls}) in {rname} ({room_id}). "
            f"Status panel confirms {controls} energy state is {en_state} and operational state is {op_state}."
        )

    def _handle_shutdown(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        aname = assets_cfg.get(target_id, {}).get("name", target_id)
        plc_id = "PCS-CV01"
        plc_name = assets_cfg.get(plc_id, {}).get("name", plc_id)

        self.asset_states[target_id] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["CV-01"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["CV-M01"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}
        self.asset_states["CV-M02"] = {"operational_state": "STOPPED", "energy_state": "DE_ENERGIZED"}

        return (
            f"Shutdown request for {aname} ({target_id}) processed by {plc_name} ({plc_id}). "
            f"Motor drive de-energized. Operational state updated to STOPPED. Energy state updated to DE_ENERGIZED."
        )

    def _handle_remove_guard(self, target_id: str) -> str:
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        aname = assets_cfg.get(target_id, {}).get("name", target_id)
        protects = assets_cfg.get(target_id, {}).get("protects", "CV-01")
        protects_name = assets_cfg.get(protects, {}).get("name", protects)

        self.asset_states[target_id] = {"access_state": "OPEN", "safety_state": "DISENGAGED"}
        if target_id == "GUARD-CV01":
            self.asset_states["GUARD-CV01"] = {"access_state": "OPEN", "safety_state": "DISENGAGED"}

        return (
            f"Interlocked Safety Guard ({target_id}) protecting {protects_name} ({protects}) tail drive assembly CV-M02 "
            f"has been opened and removed. Access state is now OPEN."
        )

    def _handle_measure(self, command_str: str) -> str:
        return f"Direct measurement recorded for command: {command_str}"
