from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

import httpx


class NvidiaClient:
    """NVIDIA API client for DeepSeek-V3.2 with multimodal support and robust error handling.

    Features:
    - Automatic retry with exponential backoff for rate limits (429)
    - Timeout handling for long-running requests (DeepSeek thinking time)
    - Connection error recovery
    - Multimodal support (text + images)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        timeout_s: float = 300.0,  # 5 minutes for DeepSeek thinking time
        max_retries: int = 5,
        base_retry_delay: float = 5.0,
        request_delay: float = 2.0,  # Polite delay between successful requests
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self.request_delay = request_delay
        self._last_request_time: float = 0.0

        self._client = httpx.Client(
            timeout=timeout_s,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

    def close(self) -> None:
        self._client.close()

    def _execute_with_retry(
        self,
        url: str,
        payload: dict[str, Any],
        operation_name: str = "API request"
    ) -> dict[str, Any]:
        """
        Execute API request with exponential backoff retry logic.

        Handles:
        - 429 Rate Limit: Exponential backoff (5s, 10s, 20s, 40s, 80s)
        - Timeouts: Retry with 10s delay
        - Connection errors: Retry with 10s delay
        - Polite delay: Waits between successful requests to avoid rate limits
        """
        # Polite delay between requests
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.request_delay:
                sleep_time = self.request_delay - elapsed
                time.sleep(sleep_time)

        for attempt in range(self.max_retries):
            try:
                print(f"  📡 Sending {operation_name} (Attempt {attempt + 1}/{self.max_retries})...")

                resp = self._client.post(url, json=payload)

                # Handle rate limiting (429)
                if resp.status_code == 429:
                    wait_time = self.base_retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"  ⚠️  Rate limit hit (429). Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue

                # Handle server errors (5xx) with retry
                if 500 <= resp.status_code < 600:
                    wait_time = self.base_retry_delay
                    print(f"  ⚠️  Server error ({resp.status_code}). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

                # Handle other errors
                if resp.status_code >= 400:
                    raise RuntimeError(f"NVIDIA API error {resp.status_code}: {resp.text}")

                # Success! Update last request time
                self._last_request_time = time.time()
                return resp.json()

            except httpx.TimeoutException:
                wait_time = 10.0
                print(f"  ⚠️  Timeout error. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

            except httpx.ConnectError as e:
                wait_time = 10.0
                print(f"  ⚠️  Connection error: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

            except httpx.RemoteProtocolError as e:
                wait_time = 10.0
                print(f"  ⚠️  Protocol error: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

            except Exception as e:
                # Unknown error - don't retry
                raise RuntimeError(f"Fatal error in {operation_name}: {e}") from e

        # All retries exhausted
        raise RuntimeError(f"❌ All {self.max_retries} retries failed for {operation_name}")

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Send chat completion request with multimodal support and automatic retry.

        messages format:
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Analyze this text"},
            {"role": "user", "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ]}
        ]
        """
        url = f"{self.base_url}/chat/completions"

        # Convert messages to NVIDIA format (OpenAI-compatible)
        formatted_messages = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")

            # NVIDIA API supports: system, user, assistant
            if role not in ["system", "user", "assistant"]:
                role = "user"

            formatted_messages.append({"role": role, "content": content})

        payload: dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
            "stream": False,
        }

        # Use retry logic
        data = self._execute_with_retry(url, payload, operation_name="chat completion")

        try:
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Unexpected NVIDIA response shape: {data}") from exc

    def encode_image(self, image_path: str | Path) -> str:
        """
        Encode image file to base64 data URL for multimodal input.

        Args:
            image_path: Path to image file (PNG, JPG, etc.)

        Returns:
            Data URL string: "data:image/jpeg;base64,..."
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine MIME type
        suffix = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/jpeg")

        # Read and encode
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{image_data}"

    def chat_with_image(
        self,
        *,
        model: str,
        text: str,
        image_path: str | Path,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Convenience method for chat with single image.

        Args:
            model: Model name (e.g., "nvidia/deepseek-ai/deepseek-v3.2")
            text: User question/prompt about the image
            image_path: Path to image file
            system_prompt: System instruction
            max_tokens: Max response tokens
            temperature: Sampling temperature

        Returns:
            Model response text
        """
        image_url = self.encode_image(image_path)

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

        return self.chat(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
