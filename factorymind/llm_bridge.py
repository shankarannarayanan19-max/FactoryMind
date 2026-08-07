"""
Local Ollama LLM Bridge for FactoryMind.

Everything runs locally:
- No cloud
- No API key
- No external AI service

Default model:
    qwen3:1.7b
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests


class LLMBridge:
    """Connect FactoryMind to a locally running Ollama model."""

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
        base_url: str = "http://127.0.0.1:11434",
        use_stub: bool = False,
        timeout: int = 120,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.use_stub = use_stub
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check whether the local Ollama server is running."""

        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )

            return response.status_code == 200

        except requests.RequestException:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response using the local Ollama model.

        The model is kept loaded for faster repeated interaction.
        """

        if self.use_stub:
            return self._stub_response(prompt)

        if not prompt or not prompt.strip():
            return "No prompt was provided."

        request_data: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt.strip(),
            "stream": False,

            # Keep Qwen loaded in memory for faster next responses.
            "keep_alive": "15m",

            # Optimised for fast command generation.
            "options": {
                "temperature": 0.1,
                "num_predict": 100,
                "num_ctx": 2048,
                "top_p": 0.8,
                "top_k": 20,
                "repeat_penalty": 1.05,
            },
        }

        if system_prompt:
            request_data["system"] = system_prompt.strip()

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                timeout=self.timeout,
            )

            response.raise_for_status()

            response_data = response.json()

            generated_text = str(
                response_data.get("response", "")
            ).strip()

            if not generated_text:
                return (
                    "The local Qwen model returned an empty response."
                )

            return generated_text

        except requests.Timeout:
            return (
                "Local Qwen response timed out. "
                "Try again or use a smaller Ollama model."
            )

        except requests.ConnectionError:
            return (
                "Ollama is not reachable at "
                f"{self.base_url}. Start Ollama and try again."
            )

        except requests.HTTPError as error:
            return (
                "Ollama returned an HTTP error: "
                f"{error}"
            )

        except json.JSONDecodeError:
            return (
                "Ollama returned an invalid JSON response."
            )

        except requests.RequestException as error:
            return (
                "Local Ollama request failed: "
                f"{error}"
            )

    def narrate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Compatibility method for ReportGenerator.

        Some FactoryMind modules may call narrate() instead of generate().
        """

        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )

    def generate_command(
        self,
        user_input: str,
        observation: str,
        valid_commands: str,
    ) -> str:
        """Convert natural language into one valid text-world command."""

        prompt = f"""
You are FactoryMind's local command interpreter.

Convert the user's natural-language request into exactly one valid
FactoryMind command.

Current observation:
{observation}

Valid commands:
{valid_commands}

User request:
{user_input}

Rules:
1. Return only one command.
2. Do not explain.
3. Do not use Markdown.
4. Never invent a command outside the valid command list.
5. If the user is only greeting, return: chat

Command:
""".strip()

        response = self.generate(prompt)

        cleaned_response = (
            response
            .replace("```json", "")
            .replace("```text", "")
            .replace("```", "")
            .strip()
        )

        if not cleaned_response:
            return "look"

        return cleaned_response.splitlines()[0].strip()

    def _stub_response(self, prompt: str) -> str:
        """Fallback response used only when stub mode is enabled."""

        return (
            "FactoryMind local fallback response. "
            "Ollama reasoning is currently disabled."
        )