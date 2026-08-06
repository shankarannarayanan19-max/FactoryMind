"""Preprocessing & Parsing module for FactoryMind."""

from typing import Dict, Any, List

class TextParser:
    def __init__(self, llm_bridge=None):
        self.llm_bridge = llm_bridge

    def parse(self, raw_text: str) -> List[Dict[str, Any]]:
        """Preprocess and parse raw observation text into structured candidate facts."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        parsed_facts = []
        for line in lines:
            parsed_facts.append({
                "raw_evidence": line,
                "confidence": 1.0,
                "source": "deterministic_parser",
                "parsed": True
            })
        return parsed_facts
