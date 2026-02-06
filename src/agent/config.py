from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    llm_provider: str = Field(default="gemini")  # gemini only
    hf_token: str | None = Field(default=None)
    hf_model: str = Field(default="meta-llama/Meta-Llama-3-8B-Instruct")

    gemini_api_key: str | None = Field(default=None)
    gemini_model: str = Field(default="gemini-1.5-flash")

    system_prompt: str = Field(default="You are a helpful assistant.")


def load_settings() -> Settings:
    load_dotenv(override=False)

    llm_provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower() or "gemini"

    hf_token = os.getenv("HF_TOKEN", "").strip() or None
    hf_model = os.getenv("HF_MODEL", "").strip() or Settings().hf_model

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
    gemini_model = os.getenv("GEMINI_MODEL", "").strip() or Settings().gemini_model

    system_prompt = os.getenv("AGENT_SYSTEM_PROMPT", "").strip() or Settings().system_prompt

    if llm_provider == "gemini":
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
        system_prompt=system_prompt,
    )
