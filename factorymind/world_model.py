"""Persistent World Model for FactoryMind."""

from typing import Dict, Any, List

class WorldModel:
    def __init__(self):
        self.factory = {}
        self.agent = {"location": "UNKNOWN"}
        self.rooms: Dict[str, Any] = {}
        self.assets: Dict[str, Any] = {}
        self.relationships: List[Dict[str, Any]] = []
        self.latest_measurements: Dict[str, Any] = {}
        self.measurement_history: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []
        self.mission_state: Dict[str, Any] = {}
        self.action_history: List[Dict[str, Any]] = []
        self.reports: List[Dict[str, Any]] = []
