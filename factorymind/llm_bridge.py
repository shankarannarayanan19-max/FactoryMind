"""LLM Bridge for FactoryMind (§14 & §19).

Hard Rule: Local LLM is confined to two roles only:
(a) Fallback natural-language parsing when deterministic regex fails.
(b) Turning already-finalized JSON facts into human-readable prose.

The LLM is NEVER allowed to set asset health_state, override thresholds,
approve/deny safety actions, or invent entities/measurements.
"""

import re
from typing import Dict, Any, Optional
from factorymind.config_loader import ConfigLoader

class LLMBridge:
    def __init__(self, model_path: Optional[str] = None, use_stub: bool = True, config_loader: Optional[ConfigLoader] = None):
        self.model_path = model_path
        self.use_stub = use_stub
        self._model = None
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader

        if not use_stub and model_path:
            try:
                # pyrefly: ignore [missing-import]
                from llama_cpp import Llama
                self._model = Llama(model_path=model_path, verbose=False)
            except Exception:
                self.use_stub = True
        else:
            self.use_stub = True

    def _extract_all_numbers(self, data: Any) -> set:
        """Extract all numeric values (as float/str) present in a JSON/dict structure."""
        nums = set()
        if isinstance(data, dict):
            for k, v in data.items():
                nums.update(self._extract_all_numbers(v))
        elif isinstance(data, list):
            for item in data:
                nums.update(self._extract_all_numbers(item))
        elif isinstance(data, (int, float)):
            nums.add(str(data))
            nums.add(f"{float(data):.1f}")
        elif isinstance(data, str):
            # Find numbers in string values
            matches = re.findall(r'\b\d+(?:\.\d+)?\b', data)
            nums.update(matches)
        return nums

    def narrate(self, facts_json: Dict[str, Any]) -> str:
        """Turn finalized JSON facts into human-readable prose matching §19 Output 3.
        Must use only numbers/IDs in facts_json and never invent facts.
        """
        valid_numbers = self._extract_all_numbers(facts_json)

        if self._model and not self.use_stub:
            prompt = (
                "You are an industrial factory inspection assistant. "
                "Describe the following finalized inspection facts in clear prose. "
                "Do NOT invent any values, asset IDs, or measurements not in the JSON.\n"
                f"Facts JSON: {facts_json}\nAnswer:"
            )
            response = self._model(prompt, max_tokens=256, temperature=0.0)
            raw_prose = response["choices"][0]["text"].strip()
            
            # Hallucination filter: verify prose contains only valid numbers from facts_json
            prose_nums = set(re.findall(r'\b\d+(?:\.\d+)?\b', raw_prose))
            hallucinated_nums = prose_nums - valid_numbers
            if hallucinated_nums:
                # Reject hallucination and return deterministic narration
                return self._deterministic_narrate(facts_json)
            return raw_prose
        
        return self._deterministic_narrate(facts_json)

    def _deterministic_narrate(self, facts_json: Dict[str, Any]) -> str:
        """Fallback deterministic narration strictly adhering to facts_json values."""
        entity = facts_json.get("entity_id") or facts_json.get("asset_id") or "Asset"
        status = facts_json.get("health_state") or facts_json.get("status") or facts_json.get("telemetry_status") or "NORMAL"
        reasons = facts_json.get("reasons", [])
        telemetry = facts_json.get("telemetry") or facts_json.get("latest_measurements") or {}

        prose = f"Asset {entity} is currently {status}."
        if reasons:
            prose += f" Observed issues: {'; '.join(reasons)}."
        if telemetry:
            val = telemetry.get("value")
            unit = telemetry.get("unit", "")
            if val is not None:
                prose += f" Telemetry reading: {val} {unit}."

        return f"[Narrative Report] {prose}"

    def assist_parse(self, sentence: str) -> Dict[str, Any]:
        """Fallback NL extraction when regex finds no matches.
        Output MUST be validated against the known ontology/registry before being trusted.
        """
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})
        known_ontology_ids = set(assets_cfg.keys()).union(sensors_cfg.keys())

        candidate_ids = re.findall(r'\b([A-Z]{2,5}-[A-Z0-9-]+)\b', sentence)
        valid_candidates = [cid for cid in candidate_ids if cid in known_ontology_ids]
        invalid_candidates = [cid for cid in candidate_ids if cid not in known_ontology_ids]

        if self._model and not self.use_stub:
            prompt = (
                "Extract facts from the following observation into JSON. "
                "Only extract entity names, locations, and sensor values explicitly stated.\n"
                f"Sentence: '{sentence}'\nJSON:"
            )
            response = self._model(prompt, max_tokens=128, temperature=0.0)
            text = response["choices"][0]["text"].strip()
            
            # Reject candidates not in ontology
            for inv in invalid_candidates:
                if inv in text:
                    text = text.replace(inv, "[REJECTED_UNKNOWN_ENTITY]")

            return {
                "raw_response": text,
                "valid_entities": valid_candidates,
                "rejected_entities": invalid_candidates,
                "source": "llm_fallback_validated"
            }

        return {
            "raw_response": sentence,
            "valid_entities": valid_candidates,
            "rejected_entities": invalid_candidates,
            "source": "llm_stub_fallback_validated"
        }

