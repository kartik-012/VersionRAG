"""
Dynamic Runtime LLM & Embedding Provider Switcher Service.

Allows users or technical interviewers to switch between:
1. `local_deterministic` (Default — zero API key required, 100% deterministic grounded synthesis)
2. `gemini` (Google Gemini `gemini-1.5-pro` / `gemini-2.0-flash`)
3. `openai` (OpenAI `gpt-4o-mini` / `gpt-4o`)
4. `anthropic` (Anthropic `claude-3-5-sonnet-latest`)
5. `groq` (Groq `llama-3.3-70b-versatile`)

at runtime directly from the UI Navbar or REST API without restarting the server.
"""

from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings


SUPPORTED_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "local_deterministic",
        "name": "Local Deterministic Engine",
        "default_model": "VersionRAG-v1-Deterministic",
        "requires_key": False,
        "badge": "Zero-Key Offline",
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "default_model": "gemini-1.5-pro",
        "requires_key": True,
        "badge": "Google AI",
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "requires_key": True,
        "badge": "OpenAI API",
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "default_model": "claude-3-5-sonnet-latest",
        "requires_key": True,
        "badge": "Anthropic API",
    },
    {
        "id": "groq",
        "name": "Groq Cloud LPU",
        "default_model": "llama-3.3-70b-versatile",
        "requires_key": True,
        "badge": "Ultra-Fast LPU",
    },
]


class LLMProviderService:
    def __init__(self):
        self._active_provider: str = "local_deterministic"
        self._active_model: str = "VersionRAG-v1-Deterministic"
        self._api_keys: Dict[str, str] = {}

        if settings.GEMINI_API_KEY:
            self._api_keys["gemini"] = settings.GEMINI_API_KEY
        if settings.OPENAI_API_KEY:
            self._api_keys["openai"] = settings.OPENAI_API_KEY
        if getattr(settings, "ANTHROPIC_API_KEY", None):
            self._api_keys["anthropic"] = settings.ANTHROPIC_API_KEY

    @staticmethod
    def _mask_key(key: Optional[str]) -> Optional[str]:
        if not key or len(key) < 6:
            return None
        return f"{key[:4]}...{key[-4:]}"

    def get_config(self) -> Dict[str, Any]:
        active_key = self._api_keys.get(self._active_provider)
        return {
            "active_provider": self._active_provider,
            "active_model": self._active_model,
            "has_api_key": bool(active_key) or self._active_provider == "local_deterministic",
            "masked_api_key": self._mask_key(active_key),
            "configured_providers": [p for p, k in self._api_keys.items() if k],
            "supported_providers": SUPPORTED_PROVIDERS,
        }

    def update_config(
        self,
        provider: str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider_clean = provider.strip().lower()
        valid_ids = {p["id"] for p in SUPPORTED_PROVIDERS}
        if provider_clean not in valid_ids:
            raise ValueError(f"Unsupported provider '{provider}'. Valid options: {sorted(valid_ids)}")

        self._active_provider = provider_clean

        default_model = next(
            (p["default_model"] for p in SUPPORTED_PROVIDERS if p["id"] == provider_clean),
            "VersionRAG-v1-Deterministic",
        )
        self._active_model = (model_name or "").strip() or default_model

        if api_key is not None and api_key.strip():
            clean_key = api_key.strip()
            self._api_keys[provider_clean] = clean_key

            # Synchronize with settings for embedding_service live tiering
            if provider_clean == "gemini":
                settings.GEMINI_API_KEY = clean_key
                settings.USE_MOCK_AI_IF_NO_KEY = False
            elif provider_clean == "openai":
                settings.OPENAI_API_KEY = clean_key
                settings.USE_MOCK_AI_IF_NO_KEY = False
            elif provider_clean == "anthropic":
                settings.ANTHROPIC_API_KEY = clean_key

        if provider_clean == "local_deterministic":
            settings.USE_MOCK_AI_IF_NO_KEY = True

        return self.get_config()

    def generate_live_answer(
        self,
        question: str,
        target_version: Optional[str],
        evidence_context: str,
        conflict_summary: Optional[str] = None,
    ) -> Optional[str]:
        """
        If an external LLM provider (`gemini`, `openai`, `anthropic`, `groq`) is active and has an API key,
        executes a grounded completion call. Returns None if `local_deterministic` is active or if the call fails,
        allowing seamless fallback to the deterministic synthesizer.
        """
        if self._active_provider == "local_deterministic":
            return None

        api_key = self._api_keys.get(self._active_provider)
        if not api_key:
            return None

        system_prompt = (
            "You are VersionRAG, a strict version-aware technical documentation assistant. "
            "Answer the user's question using ONLY the provided version-partitioned evidence chunks. "
            f"Target Version Lock: {target_version or 'all'}. "
            "Always cite version tags (e.g., [v15.14.0]) and highlight any breaking or silent AST changes."
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Target Version: {target_version or 'all'}\n"
            f"Conflict Alert: {conflict_summary or 'None'}\n\n"
            f"Verified Documentation Evidence:\n{evidence_context}"
        )

        try:
            if self._active_provider == "gemini":
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{self._active_model}:generateContent?key={api_key}"
                )
                payload = {
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
                    ],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 900},
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        candidates = resp.json().get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and parts[0].get("text"):
                                return parts[0]["text"]

            elif self._active_provider in ("openai", "groq"):
                base_url = (
                    "https://api.groq.com/openai/v1/chat/completions"
                    if self._active_provider == "groq"
                    else "https://api.openai.com/v1/chat/completions"
                )
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self._active_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 900,
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(base_url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        choices = resp.json().get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content")

            elif self._active_provider == "anthropic":
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self._active_model,
                    "max_tokens": 900,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        content_blocks = resp.json().get("content", [])
                        if content_blocks and content_blocks[0].get("text"):
                            return content_blocks[0]["text"]
        except Exception:
            return None

        return None


llm_provider_service = LLMProviderService()
