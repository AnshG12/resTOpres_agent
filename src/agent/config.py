from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    llm_provider: str = Field(default="nvidia")  # nvidia (primary), gemini, or hf
    hf_token: str | None = Field(default=None)
    hf_model: str = Field(default="meta-llama/Meta-Llama-3-8B-Instruct")

    gemini_api_key: str | None = Field(default=None)
    gemini_model: str = Field(default="gemini-1.5-flash")

    nvidia_api_key: str | None = Field(default=None)
    nvidia_model: str = Field(default="nvidia/deepseek-ai/deepseek-v3.2")
    nvidia_base_url: str = Field(default="https://integrate.api.nvidia.com/v1")

    system_prompt: str = Field(default="You are a helpful assistant.")


def load_settings() -> Settings:
    load_dotenv(override=False)

    llm_provider = os.getenv("LLM_PROVIDER", "nvidia").strip().lower() or "nvidia"

    hf_token = os.getenv("HF_TOKEN", "").strip() or None
    hf_model = os.getenv("HF_MODEL", "").strip() or Settings().hf_model

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
    gemini_model = os.getenv("GEMINI_MODEL", "").strip() or Settings().gemini_model

    nvidia_api_key = os.getenv("NVIDIA_API_KEY", "").strip() or None
    nvidia_model = os.getenv("NVIDIA_MODEL", "").strip() or Settings().nvidia_model
    nvidia_base_url = os.getenv("NVIDIA_BASE_URL", "").strip() or Settings().nvidia_base_url

    system_prompt = os.getenv("AGENT_SYSTEM_PROMPT", "").strip() or Settings().system_prompt

    if llm_provider == "nvidia":
        if not nvidia_api_key:
            raise RuntimeError(
                "Missing NVIDIA_API_KEY. Set NVIDIA_API_KEY=... in your .env for NVIDIA DeepSeek."
            )
    elif llm_provider == "gemini":
        if not gemini_api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Set GEMINI_API_KEY=... in your .env for Gemini."
            )
    elif llm_provider == "hf":
        if not hf_token:
            raise RuntimeError(
                "Missing HF_TOKEN. Create a .env from .env.example and set HF_TOKEN=..."
            )
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {llm_provider}")

    return Settings(
        llm_provider=llm_provider,
        hf_token=hf_token,
        hf_model=hf_model,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        nvidia_api_key=nvidia_api_key,
        nvidia_model=nvidia_model,
        nvidia_base_url=nvidia_base_url,
        system_prompt=system_prompt,
    )
