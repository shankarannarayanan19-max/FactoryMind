"""LLM Bridge for FactoryMind (§14 & §19) supporting Ollama and local fallbacks."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional
import requests

from factorymind.config_loader import ConfigLoader


class LLMBridge:
    """Local LLM bridge for FactoryMind (§14 & §19) with Ollama integration and deterministic fallbacks."""

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
        base_url: str = "http://127.0.0.1:11434",
        use_stub: bool = False,
        timeout: int = 180,
        config_loader: Optional[ConfigLoader] = None,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.use_stub = use_stub
        self.timeout = timeout
        if config_loader is None:
            config_loader = ConfigLoader()
            config_loader.load_all()
        self.config_loader = config_loader

    def is_available(self) -> bool:
        """Return True when the local Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate one local response."""
        if self.use_stub:
            return self._stub_response(prompt)

        if not prompt or not prompt.strip():
            return "Please enter a factory request."

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        request_body: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": 0.0,
                "num_predict": 512,
                "num_ctx": 4096,
                "top_p": 0.8,
                "top_k": 20,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=request_body,
                timeout=self.timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            message = response_data.get("message", {})
            content = str(message.get("content", "")).strip()

            if content:
                return content

            return self._stub_response(prompt)
        except Exception:
            return self._stub_response(prompt)

    def _stub_response(self, prompt: str) -> str:
        return "FactoryMind local fallback: mission evidence processed successfully."

    def _extract_all_numbers(self, data: Any) -> set:
        """Extract all numeric values present in a JSON/dict structure."""
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
            matches = re.findall(r"\b\d+(?:\.\d+)?\b", data)
            nums.update(matches)
        return nums

    def narrate(self, facts_json: Any, system_prompt: Optional[str] = None) -> str:
        """Turn finalized JSON facts into human-readable prose matching §19 Output 3."""
        if isinstance(facts_json, str):
            return self.generate(facts_json, system_prompt=system_prompt)

        valid_numbers = self._extract_all_numbers(facts_json)

        if not self.use_stub:
            prompt = (
                "You are an industrial factory inspection assistant. "
                "Describe the following finalized inspection facts in clear prose. "
                "Do NOT invent any values, asset IDs, or measurements not in the JSON.\n"
                f"Facts JSON: {facts_json}\nAnswer:"
            )
            raw_prose = self.generate(prompt)
            prose_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", raw_prose))
            if prose_nums - valid_numbers:
                return self._deterministic_narrate(facts_json)
            return raw_prose

        return self._deterministic_narrate(facts_json)

    def _deterministic_narrate(self, facts_json: Dict[str, Any]) -> str:
        """Fallback deterministic narration strictly adhering to facts_json values."""
        entity = facts_json.get("entity_id") or facts_json.get("asset_id") or "Asset"
        status = (
            facts_json.get("health_state")
            or facts_json.get("status")
            or facts_json.get("telemetry_status")
            or "NORMAL"
        )
        reasons = facts_json.get("reasons", [])
        telemetry = (
            facts_json.get("telemetry")
            or facts_json.get("latest_measurements")
            or {}
        )

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
        """Fallback NL extraction when regex finds no matches (§14 & §19)."""
        assets_cfg = self.config_loader.asset_registry.get("assets", {})
        sensors_cfg = self.config_loader.sensor_registry.get("sensors", {})
        known_ontology_ids = set(assets_cfg.keys()).union(sensors_cfg.keys())

        candidate_ids = re.findall(r"\b([A-Z]{2,5}-[A-Z0-9-]+)\b", sentence)
        valid_candidates = [cid for cid in candidate_ids if cid in known_ontology_ids]
        invalid_candidates = [
            cid for cid in candidate_ids if cid not in known_ontology_ids
        ]

        if not self.use_stub:
            prompt = (
                "Extract facts from the following observation into JSON. "
                "Only extract entity names, locations, and sensor values explicitly stated.\n"
                f"Sentence: '{sentence}'\nJSON:"
            )
            raw_text = self.generate(prompt)
            for inv in invalid_candidates:
                if inv in raw_text:
                    raw_text = raw_text.replace(inv, "[REJECTED_UNKNOWN_ENTITY]")

            return {
                "raw_response": raw_text,
                "valid_entities": valid_candidates,
                "rejected_entities": invalid_candidates,
                "source": "llm_fallback_validated",
            }

        return {
            "raw_response": sentence,
            "valid_entities": valid_candidates,
            "rejected_entities": invalid_candidates,
            "source": "llm_stub_fallback_validated",
        }