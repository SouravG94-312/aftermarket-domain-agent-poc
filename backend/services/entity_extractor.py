from __future__ import annotations

import re

from observability.langsmith_tracing import trace_agent


@trace_agent("entity_extraction", run_type="chain", tags=["routing"])
def extract_entities(text: str, previous: dict[str, str] | None = None) -> dict[str, str]:
    previous = previous or {}
    t = text.upper()
    entities: dict[str, str] = {}

    claim = re.search(r"\b(WC\d{3,})\b", t)
    if claim:
        entities["claim_id"] = claim.group(1)

    dealer = re.search(r"\b(DLR\d{3,})\b", t)
    if dealer:
        entities["dealer_id"] = dealer.group(1)

    vin = re.search(r"\b(VIN[A-Z0-9]{6,})\b", t)
    if vin:
        entities["vin"] = vin.group(1)

    part = re.search(r"\b(P\d{3,})\b", t)
    if part:
        entities["part_number"] = part.group(1)

    market_map = {
        "GERMANY": "DE", "DE": "DE", "FRANCE": "FR", "FR": "FR",
        "ITALY": "IT", "IT": "IT", "SPAIN": "ES", "ES": "ES",
        "NETHERLANDS": "NL", "NL": "NL", "UK": "UK", "UNITED KINGDOM": "UK"
    }
    for key, val in market_map.items():
        if re.search(rf"\b{re.escape(key)}\b", t):
            entities["market_code"] = val
            break

    # Multi-turn follow-up support: inherit missing values from previous context.
    for key in ["claim_id", "dealer_id", "vin", "part_number", "market_code"]:
        if key not in entities and key in previous:
            entities[key] = previous[key]

    return entities
