from __future__ import annotations

import os
from typing import Any

import httpx


class GeminiClient:
    """Minimal Gemini client using REST API.

    Expects messages as list of {"role": "user"|"assistant"|"system", "content": str}.
    Converts to Gemini generateContent format.
    """

    def __init__(self, api_key: str, timeout_s: float = 60.0) -> None:
        self.api_key = api_key
        self._client = httpx.Client(timeout=timeout_s, headers={"Content-Type": "application/json"})

    def close(self) -> None:
        self._client.close()

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        # Gemini REST expects bare model ids (e.g., "gemini-1.5-flash"); strip any leading
        # "models/" prefix to avoid 404s from double-prefixing. Default to the stable v1
        # endpoint; allow override via GEMINI_API_VERSION if needed.
        api_version = os.getenv("GEMINI_API_VERSION", "v1").strip() or "v1"
        model_id = model.removeprefix("models/")
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_id}:generateContent?key={self.api_key}"

        contents = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "")

            # Gemini roles are "user" and "model"; map system to user with prefix.
            if role == "assistant":
                gemini_role = "model"
                gemini_text = text
            elif role == "system":
                gemini_role = "user"
                gemini_text = f"[SYSTEM]\n{text}"
            else:
                gemini_role = "user"
                gemini_text = text

            contents.append({"role": gemini_role, "parts": [{"text": gemini_text}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        resp = self._client.post(url, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Unexpected Gemini response shape: {data}") from exc
