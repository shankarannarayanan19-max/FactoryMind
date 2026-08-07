"""Preprocessing & Parsing module for FactoryMind.

Hard Rules:
1. All parsed facts must retain `raw_evidence` (untouched original sentence).
2. Deterministic regex & room detection rules must be strictly ordered.
3. LLM is invoked strictly as fallback when regex yields zero matches.
"""

import re
from typing import Dict, Any, List, Optional
from factorymind.config_loader import ConfigLoader
from factorymind.llm_bridge import LLMBridge

# Standard Unit Normalization Mapping
UNIT_MAP = {
    r'\bdeg\s*C\b': 'C',
    r'\bcelsius\b': 'C',
    r'\bdegC\b': 'C',
    r'\bdegree\s*celsius\b': 'C',
    r'\bmm/sec\b': 'mm/s',
    r'\bmm\s*/\s*s\b': 'mm/s',
    r'\bmm\s*/\s*sec\b': 'mm/s',
    r'\bvolts\b': 'V',
    r'\bvdc\b': 'V',
    r'\bvac\b': 'V',
    r'\bamps\b': 'A',
    r'\bamperes\b': 'A',
}

# Regex Patterns
ID_PATTERN = re.compile(r'\b([A-Z]{2,5}-[A-Z0-9-]+)\b')
NUMERIC_READING_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*(C|mm/s|bar|psi|V|A|kW|RPM|C|celsius|mm/sec)\b',
    re.IGNORECASE
)
STATE_WORD_PATTERN = re.compile(
    r'\b(RUNNING|STOPPED|ENERGIZED|DE_ENERGIZED|OPEN|CLOSED|WARNING|CRITICAL|NORMAL|DISENGAGED|ENGAGED|ELEVATED_TEMPERATURE|SEVERE_VIBRATION)\b',
    re.IGNORECASE
)

class TextParser:
    def __init__(self, config_loader: Optional[ConfigLoader] = None, llm_bridge: Optional[LLMBridge] = None):
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader
        self.llm_bridge = llm_bridge or LLMBridge(use_stub=True)

    def standardize_units(self, text: str) -> str:
        """Standardize unit representations in text."""
        result = text
        for pattern, replacement in UNIT_MAP.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    def preprocess(self, raw_text: str) -> List[Dict[str, str]]:
        """Preprocess raw text: blank-line removal, unit standardization, sentence splitting.
        Returns list of dicts with 'raw_evidence' and 'normalized_text'.
        """
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        processed_sentences = []

        for line in lines:
            # Split line into sentences on period or semicolon followed by space
            raw_sentences = [s.strip() for s in re.split(r'(?<=[.;])\s+', line) if s.strip()]
            for raw_sent in raw_sentences:
                normalized = self.standardize_units(raw_sent)
                processed_sentences.append({
                    "raw_evidence": raw_sent,
                    "normalized_text": normalized
                })

        return processed_sentences

    def detect_room(
        self,
        observation: str,
        nav_intent: Optional[Dict[str, str]] = None,
        prev_room: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect current room adhering strictly to the 5-tier confidence hierarchy:
        1. Explicit room sentence (conf: 1.0, source: deterministic_parser)
        2. Valid navigation inference (conf: 0.90, source: navigation_inference)
        3. Unique asset-location evidence (conf: 0.85, source: asset_location_inference)
        4. Previous known room (conf: 0.70, source: previous_known_room)
        5. UNKNOWN -> trigger 'look' recommendation
        """
        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})

        # Tier 1: Explicit room sentence / header
        loc_match = re.search(r'Location:\s*(?:[^(]+)\((ROOM-[A-Z0-9-]+)\)', observation)
        if loc_match:
            detected = loc_match.group(1)
            if detected in rooms_cfg:
                return {
                    "room": detected,
                    "confidence": 1.0,
                    "source": "deterministic_parser",
                    "tier": 1
                }

        for room_id, rdata in rooms_cfg.items():
            rname = rdata.get("name", "")
            if room_id in observation or (rname and rname in observation):
                if f"Location: {rname}" in observation or f"({room_id})" in observation or f"in {rname}" in observation or f"located in {rname}" in observation:
                    return {
                        "room": room_id,
                        "confidence": 1.0,
                        "source": "deterministic_parser",
                        "tier": 1
                    }

        # Tier 2: Valid navigation inference
        if nav_intent and prev_room and prev_room in rooms_cfg:
            direction = nav_intent.get("direction")
            exits = rooms_cfg[prev_room].get("exits", {})
            if direction in exits:
                target_room = exits[direction]
                return {
                    "room": target_room,
                    "confidence": 0.90,
                    "source": "navigation_inference",
                    "tier": 2
                }

        # Tier 3: Unique asset-location evidence
        # Check for asset or sensor IDs in observation
        found_ids = ID_PATTERN.findall(observation)
        for entity_id in found_ids:
            if entity_id in assets_cfg:
                assigned_room = assets_cfg[entity_id].get("room")
                if assigned_room:
                    return {
                        "room": assigned_room,
                        "confidence": 0.85,
                        "source": "asset_location_inference",
                        "tier": 3
                    }
            elif entity_id in sensors_cfg:
                assigned_room = sensors_cfg[entity_id].get("room")
                if assigned_room:
                    return {
                        "room": assigned_room,
                        "confidence": 0.85,
                        "source": "asset_location_inference",
                        "tier": 3
                    }

        # Tier 4: Previous known room
        if prev_room and prev_room in rooms_cfg:
            return {
                "room": prev_room,
                "confidence": 0.70,
                "source": "previous_known_room",
                "tier": 4
            }

        # Tier 5: UNKNOWN
        return {
            "room": "UNKNOWN",
            "confidence": 0.0,
            "source": "unknown",
            "tier": 5,
            "recommendation": "look"
        }

    def check_impossible_transition(self, prev_room: str, new_room: str) -> Optional[Dict[str, Any]]:
        """Emit LOCATION_TRANSITION_CONFLICT event if topology does not connect prev_room and new_room."""
        if not prev_room or not new_room or prev_room == "UNKNOWN" or new_room == "UNKNOWN":
            return None
        if prev_room == new_room:
            return None

        rooms_cfg = self.config_loader.factory_map.get("rooms", {})
        if prev_room not in rooms_cfg:
            return None

        connected_rooms = list(rooms_cfg[prev_room].get("exits", {}).values())
        if new_room not in connected_rooms:
            return {
                "event_type": "LOCATION_TRANSITION_CONFLICT",
                "severity": "WARNING",
                "prev_room": prev_room,
                "observed_room": new_room,
                "description": f"Impossible transition from {prev_room} to {new_room}. Rooms are not connected in factory map."
            }

        return None

    def parse_sentence(self, sentence_obj: Dict[str, str]) -> Dict[str, Any]:
        """Parse an individual sentence for IDs, numeric readings, state words, and rooms.
        Falls back to LLM ONLY when regex yields zero matches.
        """
        raw = sentence_obj["raw_evidence"]
        text = sentence_obj["normalized_text"]

        ids = ID_PATTERN.findall(text)
        readings = NUMERIC_READING_PATTERN.findall(text)
        state_words = STATE_WORD_PATTERN.findall(text)

        has_regex_match = bool(ids or readings or state_words)

        if has_regex_match:
            return {
                "raw_evidence": raw,
                "normalized_text": text,
                "extracted_ids": ids,
                "numeric_readings": readings,
                "state_words": state_words,
                "source": "deterministic_parser",
                "confidence": 1.0
            }
        else:
            # Fallback to LLM
            llm_res = self.llm_bridge.assist_parse(raw)
            return {
                "raw_evidence": raw,
                "normalized_text": text,
                "llm_result": llm_res,
                "source": "llm_fallback",
                "confidence": 0.50
            }

    def parse_observation(
        self,
        observation: str,
        nav_intent: Optional[Dict[str, str]] = None,
        prev_room: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parse complete observation text into preprocessed sentences, detected room, and extracted facts."""
        sentences = self.preprocess(observation)
        room_info = self.detect_room(observation, nav_intent, prev_room)

        # Check for transition conflict
        transition_conflict = None
        if prev_room and room_info["room"] != "UNKNOWN":
            transition_conflict = self.check_impossible_transition(prev_room, room_info["room"])

        parsed_facts = [self.parse_sentence(s) for s in sentences]

        return {
            "room_info": room_info,
            "transition_conflict": transition_conflict,
            "parsed_facts": parsed_facts
        }
