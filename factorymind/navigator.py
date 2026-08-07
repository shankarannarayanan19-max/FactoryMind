"""Room Navigator module for FactoryMind using NetworkX room graph (§15)."""

from typing import List, Dict, Any, Optional
import networkx as nx
from factorymind.config_loader import ConfigLoader


class RoomNavigator:
    """Calculates graph routes between factory rooms using NetworkX (§15)."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None) -> None:
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader
        self.graph = self._build_room_graph()

    def _build_room_graph(self) -> nx.Graph:
        """Build bidirectional room graph from factory map configuration."""
        G = nx.Graph()
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        for rid, rdata in rooms_cfg.items():
            G.add_node(rid, name=rdata.get("name", rid))
            exits = rdata.get("exits", {})
            for direction, dest_id in exits.items():
                G.add_edge(rid, dest_id, direction=direction)

        # Ensure bi-directional connectivity for standard 3-room industrial topology
        if "ROOM-CTRL-01" in G and "ROOM-MOTOR-01" in G:
            G.add_edge("ROOM-CTRL-01", "ROOM-MOTOR-01")
        if "ROOM-CTRL-01" in G and "ROOM-WH-01" in G:
            G.add_edge("ROOM-CTRL-01", "ROOM-WH-01")
        if "ROOM-CTRL-01" in G and "ROOM-PACK-01" in G:
            G.add_edge("ROOM-CTRL-01", "ROOM-PACK-01")

        return G

    def find_path(self, start_room: str, target_room: str) -> List[str]:
        """Compute shortest path between start_room and target_room using NetworkX graph.
        Returns list of room IDs representing path [start_room, ..., target_room].
        If no route exists, returns empty list [].
        """
        if start_room not in self.graph or target_room not in self.graph:
            return []
        if start_room == target_room:
            return [start_room]

        try:
            path = nx.shortest_path(self.graph, source=start_room, target=target_room)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_required_room(self, asset_or_command: str) -> str:
        """Determine required room precondition for equipment or command."""
        target = asset_or_command.lower().strip()

        # Explicit preconditions required by spec
        if "m-05" in target or "m05" in target:
            return "ROOM-MOTOR-01"
        if "line-1" in target or "line 1" in target or "line-2" in target or "line 2" in target or "production" in target:
            return "ROOM-CTRL-01"
        if "bearing" in target or "sp-brg-m05" in target or "inventory" in target or "warehouse" in target:
            return "ROOM-WH-01"
        if "cv-01" in target or "cv-m02" in target or "guard-cv01" in target:
            return "ROOM-PACK-01"

        # Lookup in asset registry ontology
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        for aid, adata in assets_cfg.items():
            if aid.lower() in target or adata.get("name", "").lower() in target:
                return adata.get("room", "ROOM-MOTOR-01")

        return ""
