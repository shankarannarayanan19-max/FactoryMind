"""Local Ollama bridge for FactoryMind."""

from __future__ import annotations

import json
from typing import Any, Dict

import requests


class LLMBridge:
    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        base_url: str = "http://127.0.0.1:11434",
        use_stub: bool = False,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.use_stub = use_stub

    def generate(self, prompt: str) -> str:
        if self.use_stub:
            return self._stub_response(prompt)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2
                    },
                },
                timeout=120,
            )
            response.raise_for_status()

            data: Dict[str, Any] = response.json()
            return str(data.get("response", "")).strip()

        except requests.RequestException as exc:
            print(f"[Ollama unavailable: {exc}]")
            return self._stub_response(prompt)

        except json.JSONDecodeError:
            print("[Ollama returned an invalid response]")
            return self._stub_response(prompt)

    def _stub_response(self, prompt: str) -> str:
        return (
            "FactoryMind local fallback: mission evidence was processed "
            "successfully, but Ollama was unavailable."
        )