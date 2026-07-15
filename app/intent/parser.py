from __future__ import annotations

from app.intent.deterministic_parser import parse_intent
from app.models.intent import ServiceIntent


def parse_service_intent(text: str, llm_result: dict | None = None) -> ServiceIntent:
    if llm_result is not None:
        try:
            return ServiceIntent.model_validate(llm_result)
        except Exception:
            pass
    return parse_intent(text)
