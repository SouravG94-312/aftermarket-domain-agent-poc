from __future__ import annotations
from config.settings import settings
from db.sql_client import sql_client

def get_warranty_claim_details_impl(claim_id: str) -> dict:
    claim_id = claim_id.strip().upper()
    query = f"""
    SELECT claim_id, dealer_id, dealer_name, market_code, market_name, region, vin,
           repair_order_id, claim_status, claim_type, claim_amount_eur, repair_date,
           submitted_date, decision_date, days_to_submit, claim_cycle_time_days,
           rejection_reason, missing_documents, prior_authorization_required,
           repeat_repair_flag, claim_risk_level, fault_code, symptom, component,
           parts_replaced, vehicle_off_road_hours, technical_case_created,
           recommended_claim_action
    FROM {settings.fq_schema}.vw_warranty_claim_intelligence
    WHERE upper(claim_id) = :claim_id
    LIMIT 1
    """
    row = sql_client.query_one(query, {"claim_id": claim_id})
    if not row:
        return {"found": False, "claim_id": claim_id, "message": f"No warranty claim found for '{claim_id}'."}
    return {
        "found": True,
        "claim": row,
        "summary": {
            "claim_id": row.get("claim_id"),
            "status": row.get("claim_status"),
            "risk_level": row.get("claim_risk_level"),
            "rejection_reason": row.get("rejection_reason"),
            "missing_documents": row.get("missing_documents"),
            "prior_authorization_required": row.get("prior_authorization_required"),
            "repeat_repair_flag": row.get("repeat_repair_flag"),
            "recommended_action": row.get("recommended_claim_action"),
        },
    }
