"""
Local Ollama bridge for FactoryMind.

Runs fully locally using Ollama.
No cloud API or API key is used.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class LLMBridge:
    """Connect FactoryMind to a local Ollama model."""

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
        base_url: str = "http://127.0.0.1:11434",
        use_stub: bool = False,
        timeout: int = 180,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.use_stub = use_stub
        self.timeout = timeout

    def is_available(self) -> bool:
        """Return True when the local Ollama server is running."""

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
        """Generate one local Qwen response."""

        if self.use_stub:
            return (
                '{"type":"chat",'
                '"message":"FactoryMind fallback mode is active."}'
            )

        if not prompt or not prompt.strip():
            return (
                '{"type":"chat",'
                '"message":"Please enter a factory request."}'
            )

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt.strip(),
            }
        )

        request_body: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,

            # Disable long Qwen reasoning for faster output.
            "think": False,

            # Keep model loaded for following messages.
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

            content = str(
                message.get("content", "")
            ).strip()

            if content:
                return content

            # Print useful details when Ollama returns nothing.
            done_reason = response_data.get(
                "done_reason",
                "unknown",
            )

            print(
                "\n[OLLAMA DEBUG] "
                f"Empty content. done_reason={done_reason}"
            )

            print(
                "[OLLAMA DEBUG] "
                f"Full response={response_data}"
            )

            return (
                '{"type":"chat",'
                '"message":"Qwen returned an empty response. '
                'Check the Ollama debug output above."}'
            )

        except requests.Timeout:
            return (
                '{"type":"chat",'
                '"message":"Local Qwen request timed out."}'
            )

        except requests.ConnectionError:
            return (
                '{"type":"chat",'
                '"message":"Ollama is not reachable at '
                'localhost port 11434."}'
            )

        except requests.HTTPError as error:
            return (
                '{"type":"chat",'
                f'"message":"Ollama HTTP error: {str(error)}"'
                '}'
            )

        except requests.RequestException as error:
            return (
                '{"type":"chat",'
                f'"message":"Local Ollama request failed: '
                f'{str(error)}"'
                '}'
            )

        except ValueError as error:
            return (
                '{"type":"chat",'
                f'"message":"Invalid Ollama response: '
                f'{str(error)}"'
                '}'
            )

    def narrate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Compatibility method used by ReportGenerator."""

        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )