"""LLM Bridge for FactoryMind.

Hard Rule: Local LLM is confined to two roles only:
(a) Fallback natural-language parsing when deterministic regex fails.
(b) Turning already-finalized JSON facts into human-readable prose.

The LLM is NEVER allowed to set asset health_state, override thresholds,
approve/deny safety actions, or invent entities/measurements.
"""

from typing import Dict, Any, Optional

class LLMBridge:
    def __init__(self, model_path: Optional[str] = None, use_stub: bool = False):
        self.model_path = model_path
        self.use_stub = use_stub
        self._model = None
        if not use_stub and model_path:
            try:
                from llama_cpp import Llama
                self._model = Llama(model_path=model_path, verbose=False)
            except Exception:
                self.use_stub = True
        else:
            self.use_stub = True

    def narrate(self, facts_json: Dict[str, Any]) -> str:
        """Turn finalized JSON facts into human-readable prose.
        Must use only numbers/IDs in facts_json and never invent facts.
        """
        if self._model and not self.use_stub:
            prompt = (
                "You are an industrial factory inspection assistant. "
                "Describe the following finalized inspection facts in clear prose. "
                "Do NOT invent any values, asset IDs, or measurements not in the JSON.\n"
                f"Facts JSON: {facts_json}\nAnswer:"
            )
            response = self._model(prompt, max_tokens=256, temperature=0.0)
            return response["choices"][0]["text"].strip()
        
        # Fallback/stub narration
        return f"[Narrative Report] Summary of facts: {facts_json}"

    def assist_parse(self, sentence: str) -> Dict[str, Any]:
        """Fallback NL extraction when regex finds no matches."""
        if self._model and not self.use_stub:
            prompt = (
                "Extract facts from the following observation into JSON. "
                "Only extract entity names, locations, and sensor values explicitly stated.\n"
                f"Sentence: '{sentence}'\nJSON:"
            )
            response = self._model(prompt, max_tokens=128, temperature=0.0)
            text = response["choices"][0]["text"].strip()
            return {"raw_response": text, "source": "llm_fallback"}
            
        return {"raw_response": sentence, "source": "llm_stub_fallback"}
