from __future__ import annotations

import os

from app.intent.deterministic_parser import parse_intent
from app.models.intent import ServiceIntent


def parse_with_optional_llm(text: str) -> ServiceIntent:
    provider = os.getenv("LLM_PROVIDER", "").strip()
    if not provider:
        return parse_intent(text)

    return parse_intent(text)
