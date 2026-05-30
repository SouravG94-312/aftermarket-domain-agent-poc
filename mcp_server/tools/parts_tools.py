from __future__ import annotations
from config.settings import settings
from db.sql_client import sql_client

def check_part_availability_impl(part_number: str, market_code: str | None = None, limit: int = 10) -> dict:
    part_number = part_number.strip().upper()
    market_code_clean = market_code.strip().upper() if market_code else None
    limit = max(1, min(int(limit), 50))
    query = f"""
        SELECT dealer_id, dealer_name, market_code, market_name, part_number, part_name,
               part_group_code, part_group, criticality, unit_price_eur, standard_margin_pct,
               genuine_flag, alliance_allowed_flag, reman_available_flag, stock_qty, reserved_qty,
               available_qty, backorder_qty, lead_time_days, alternate_part_number,
               reman_part_number, end_of_chain_part_number, last_updated, availability_status,
               recommended_parts_action
        FROM {settings.fq_schema}.vw_parts_availability_intelligence
        WHERE upper(part_number) = :part_number
    """
    params = {"part_number": part_number}
    if market_code_clean:
        query += " AND upper(market_code) = :market_code"
        params["market_code"] = market_code_clean
    query += f" ORDER BY available_qty DESC, lead_time_days ASC LIMIT {limit}"
    rows = sql_client.query(query, params)
    if not rows:
        return {"found": False, "part_number": part_number, "market_code": market_code_clean, "message": "No inventory record found."}
    total_available = sum((r.get("available_qty") or 0) for r in rows)
    total_backorder = sum((r.get("backorder_qty") or 0) for r in rows)
    best = rows[0]
    return {
        "found": True,
        "part_number": part_number,
        "market_code": market_code_clean,
        "summary": {
            "total_available_qty": total_available,
            "total_backorder_qty": total_backorder,
            "best_dealer": best.get("dealer_name"),
            "best_market": best.get("market_name"),
            "availability_status": best.get("availability_status"),
            "recommended_parts_action": best.get("recommended_parts_action"),
            "alternate_part_number": best.get("alternate_part_number"),
            "reman_part_number": best.get("reman_part_number"),
            "end_of_chain_part_number": best.get("end_of_chain_part_number"),
        },
        "locations": rows,
    }
