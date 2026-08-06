"""Config Loader module for FactoryMind.

Loads and validates the seven scenario configuration YAML files.
Deterministic validation rules:
1. Every asset's `room` exists in the map.
2. Every sensor's `monitors` target exists in the asset registry.
3. Every safety rule references a known action.
"""

import os
from typing import Dict, Any, Optional
import yaml

KNOWN_ACTIONS = {
    "inspect",
    "read",
    "check",
    "measure_with_tool",
    "request_shutdown",
    "create_work_order",
    "remove_guard",
    "open_panel",
    "de_energize",
    "enter_room",
}

class ConfigLoader:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, "config")
        self.config_dir = config_dir

        self.factory_map: Dict[str, Any] = {}
        self.asset_registry: Dict[str, Any] = {}
        self.sensor_registry: Dict[str, Any] = {}
        self.thresholds: Dict[str, Any] = {}
        self.safety_rules: list = []
        self.procedures: Dict[str, Any] = {}
        self.missions: list = []

    def load_all(self) -> Dict[str, Any]:
        """Load and validate all seven configuration files."""
        self.factory_map = self._load_yaml("factory_map.yaml")
        self.asset_registry = self._load_yaml("asset_registry.yaml")
        self.sensor_registry = self._load_yaml("sensor_registry.yaml")
        self.thresholds = self._load_yaml("thresholds.yaml")
        self.safety_rules = self._load_yaml("safety_rules.yaml").get("safety_rules", [])
        self.procedures = self._load_yaml("procedures.yaml")
        self.missions = self._load_yaml("missions.yaml").get("missions", [])

        self.validate()
        return {
            "factory_map": self.factory_map,
            "asset_registry": self.asset_registry,
            "sensor_registry": self.sensor_registry,
            "thresholds": self.thresholds,
            "safety_rules": self.safety_rules,
            "procedures": self.procedures,
            "missions": self.missions,
        }

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(self.config_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if content is not None else {}

    def validate(self):
        """Validate inter-config integrity constraints."""
        rooms = self.factory_map.get("rooms", {})
        assets = self.asset_registry.get("assets", {})
        sensors = self.sensor_registry.get("sensors", {})

        # Rule 1: Every asset's room exists in factory_map
        for asset_id, asset_data in assets.items():
            room_id = asset_data.get("room")
            if room_id and room_id not in rooms:
                raise ValueError(
                    f"Validation Error: Asset '{asset_id}' references unknown room '{room_id}'."
                )

        # Rule 2: Every sensor's monitors target exists in asset_registry
        for sensor_id, sensor_data in sensors.items():
            target_asset = sensor_data.get("monitors")
            if target_asset and target_asset not in assets:
                raise ValueError(
                    f"Validation Error: Sensor '{sensor_id}' monitors unknown asset '{target_asset}'."
                )

        # Rule 3: Every safety rule references a known action
        for rule in self.safety_rules:
            rule_id = rule.get("rule_id", "UNKNOWN_RULE")
            action = rule.get("action")
            if action not in KNOWN_ACTIONS:
                raise ValueError(
                    f"Validation Error: Safety rule '{rule_id}' references unknown action '{action}'."
                )
