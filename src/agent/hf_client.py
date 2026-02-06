from __future__ import annotations

from typing import Any

import httpx


class HuggingFaceClient:
    def __init__(self, token: str, timeout_s: float = 60.0) -> None:
        self._client = httpx.Client(
            timeout=timeout_s,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

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
        url = "https://api-inference.huggingface.co/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        resp = self._client.post(url, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"HF API error {resp.status_code}: {resp.text}")

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Unexpected HF response shape: {data}") from e
