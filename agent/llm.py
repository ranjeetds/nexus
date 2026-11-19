"""
LLM Interface — dynamically discovers and rotates through free public models.

Strategy:
1. Query OpenRouter for available :free models (live, refreshes hourly)
2. Round-robin through discovered models to distribute load
3. Fall back to HuggingFace Inference API (truly free, no key)
4. No hardcoded model names that can go stale — always discover first
"""

import json
import os
import time
from typing import Optional

import requests


# Only used if both OpenRouter AND HuggingFace are unreachable
ULTIMATE_FALLBACKS = [
    "mistralai/mistral-nemo",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct",
    "nvidia/nemotron-3.5-super-vl:free",
]


class LLM:
    """Multi-provider LLM with dynamic free model discovery."""

    def __init__(self, config: dict):
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)

        self.or_api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.hf_token = os.environ.get("HF_TOKEN", "")

        self._free_models: list[str] = []
        self._model_index = 0
        self._last_discovery = 0
        self._discovery_interval = 3600  # rediscover every hour

        self.last_call_time = 0
        self.min_interval = 1.5

    def _rate_limit(self):
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def discover_free_models(self) -> list[str]:
        """Query OpenRouter for all models with free prompt pricing."""
        now = time.time()
        if self._free_models and (now - self._last_discovery) < self._discovery_interval:
            return self._free_models

        if not self.or_api_key:
            self._free_models = ULTIMATE_FALLBACKS
            return self._free_models

        try:
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.or_api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                free = sorted(set(
                    m["id"] for m in data.get("data", [])
                    if m.get("pricing", {}).get("prompt") == "0"
                    and m["id"].endswith(":free")
                ))
                if free:
                    self._free_models = free
                    self._last_discovery = now
                    return free
        except Exception:
            pass

        self._free_models = ULTIMATE_FALLBACKS
        return self._free_models

    def next_model(self) -> str:
        """Round-robin through discovered free models."""
        models = self.discover_free_models()
        if not models:
            return ULTIMATE_FALLBACKS[0]
        model = models[self._model_index % len(models)]
        self._model_index += 1
        return model

    def available_models(self) -> list[str]:
        """Return list of currently discovered free models."""
        return self.discover_free_models()

    def _call_openrouter(self, prompt: str, system_prompt: str = "",
                         model: Optional[str] = None) -> Optional[str]:
        if not self.or_api_key:
            return None

        model = model or self.next_model()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.or_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexus-sovereign.app.lhr.life",
            "X-Title": "NEXUS Sovereign",
        }

        self._rate_limit()
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload, timeout=60,
            )
            self.last_call_time = time.time()

            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            # Model unavailable — skip to next
            self._model_index += 1
            return None
        except Exception:
            self._model_index += 1
            return None

    def _call_huggingface(self, prompt: str, system_prompt: str = "",
                          model: str = "microsoft/phi-2") -> Optional[str]:
        headers = {"Content-Type": "application/json"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        full_prompt = (
            f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
            if system_prompt else
            f"<s>[INST] {prompt} [/INST]"
        )

        self._rate_limit()
        try:
            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": full_prompt, "parameters": {
                    "temperature": self.temperature,
                    "max_new_tokens": self.max_tokens,
                    "return_full_text": False,
                }},
                timeout=60,
            )
            self.last_call_time = time.time()
            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", "").strip()
            return None
        except Exception:
            return None

    def generate(self, prompt: str, system_prompt: str = "",
                 model: Optional[str] = None) -> str:
        """Generate using best available free model. Rotates automatically."""
        # Try OpenRouter free models (up to 3 attempts, rotating through)
        if self.or_api_key:
            if model:
                result = self._call_openrouter(prompt, system_prompt, model)
                if result:
                    return result
            else:
                for _ in range(3):
                    result = self._call_openrouter(prompt, system_prompt)
                    if result:
                        return result

        # Fallback: HuggingFace Inference API (truly free, no key needed)
        for hf_model in ["microsoft/phi-2", "HuggingFaceH4/zephyr-7b-beta"]:
            result = self._call_huggingface(prompt, system_prompt, hf_model)
            if result:
                return result

        return "[NEXUS: All public LLM services unavailable. Waiting...]"

    def generate_json(self, prompt: str, system_prompt: str = "") -> dict:
        """Request structured JSON output. Retries with stricter prompt on failure."""
        for attempt in range(2):
            instruction = (
                "Respond ONLY with valid JSON. No markdown, no code blocks, "
                "no explanation. The entire response must be parseable as JSON."
            )
            result = self.generate(
                f"{prompt}\n\n{instruction}",
                (system_prompt or "") + " You output only valid JSON.",
            )

            for cleaner in [
                lambda s: s,
                lambda s: s.strip().removeprefix("```json").removesuffix("```").strip(),
                lambda s: s[s.find("{"):s.rfind("}")+1] if "{" in s else s,
            ]:
                try:
                    return json.loads(cleaner(result))
                except (json.JSONDecodeError, ValueError, AttributeError):
                    continue

        return {"error": "JSON parse failed", "raw": result[:500]}