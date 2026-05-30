from __future__ import annotations
from config.settings import settings
from db.sql_client import sql_client

def get_vehicle_service_history_impl(vin: str, limit: int = 10) -> dict:
    vin = vin.strip().upper()
    limit = max(1, min(int(limit), 50))
    summary_query = f"""
    SELECT vin, dealer_id, first_service_event_date, latest_service_event_date,
           total_service_events, distinct_fault_codes, distinct_symptoms,
           latest_mileage_km, fault_codes_observed, symptoms_observed, resolution_summaries
    FROM {settings.fq_schema}.vw_vehicle_service_history_summary
    WHERE upper(vin) = :vin
    LIMIT 1
    """
    events_query = f"""
    SELECT repair_order_id, dealer_id, dealer_name, market_code, market_name, vin,
           open_date, close_date, repair_duration_days, repair_status, fault_code,
           fault_description, fault_severity, recommended_first_check, escalation_rule,
           symptom, component, labor_hours, parts_replaced, repair_cost_eur,
           vehicle_off_road_hours, technical_case_created, service_priority, escalation_recommended
    FROM {settings.fq_schema}.vw_service_repair_order_intelligence
    WHERE upper(vin) = :vin
    ORDER BY open_date DESC
    LIMIT {limit}
    """
    summary = sql_client.query_one(summary_query, {"vin": vin})
    events = sql_client.query(events_query, {"vin": vin})
    if not summary and not events:
        return {"found": False, "vin": vin, "message": f"No service history found for VIN '{vin}'."}
    repeat_issue_indicator = bool(summary and (summary.get("distinct_fault_codes") or 0) < (summary.get("total_service_events") or 0))
    high_priority_events = [e for e in events if e.get("escalation_recommended") is True or "Priority 1" in str(e.get("service_priority", ""))]
    return {
        "found": True,
        "vin": vin,
        "summary": summary,
        "recent_events": events,
        "analysis": {
            "repeat_issue_indicator": repeat_issue_indicator,
            "high_priority_event_count": len(high_priority_events),
            "latest_fault_code": events[0].get("fault_code") if events else None,
            "latest_symptom": events[0].get("symptom") if events else None,
            "recommended_next_step": "Escalate to technical support due to repeat/high-priority service pattern." if high_priority_events or repeat_issue_indicator else "Follow standard troubleshooting and monitor for repeat symptoms.",
        },
    }
