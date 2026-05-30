from __future__ import annotations
from config.settings import settings
from db.sql_client import sql_client
from tools.warranty_tools import get_warranty_claim_details_impl
from tools.service_tools import get_vehicle_service_history_impl
from tools.parts_tools import check_part_availability_impl

def _dealer_context(dealer_id: str) -> dict:
    dealer_id = dealer_id.strip().upper()
    dealer = sql_client.query_one(f"SELECT * FROM {settings.fq_schema}.vw_dealer_360_summary WHERE upper(dealer_id)=:dealer_id LIMIT 1", {"dealer_id": dealer_id})
    warranty = sql_client.query(f"SELECT * FROM {settings.fq_schema}.vw_warranty_performance_summary WHERE upper(dealer_id)=:dealer_id ORDER BY claim_month DESC LIMIT 6", {"dealer_id": dealer_id})
    bonus = sql_client.query(f"SELECT * FROM {settings.fq_schema}.vw_bonus_eligibility_intelligence WHERE upper(dealer_id)=:dealer_id ORDER BY bonus_period DESC LIMIT 4", {"dealer_id": dealer_id})
    if not dealer:
        return {"found": False, "entity_type": "dealer", "entity_id": dealer_id, "message": f"No dealer found for '{dealer_id}'."}
    focus = []
    if dealer.get("eligible_flag") is False: focus.append("Bonus eligibility is blocked or at risk.")
    if (dealer.get("warranty_claim_rejection_rate") or 0) > 0.25: focus.append("Warranty rejection rate is high.")
    if (dealer.get("customer_satisfaction_score") or 5) < 4.0: focus.append("Customer satisfaction is below threshold.")
    if (dealer.get("dims_compliance_rate") or 1) < 0.70: focus.append("DIMS compliance is below entry hurdle.")
    if not focus: focus.append("No obvious critical risk found; analyze trends and opportunities.")
    return {"found": True, "entity_type": "dealer", "entity_id": dealer_id, "dealer_360": dealer, "recent_warranty_performance": warranty, "recent_bonus_records": bonus, "recommended_reasoning_focus": focus}

def _market_context(market_code: str) -> dict:
    market_code = market_code.strip().upper()
    sales = sql_client.query(f"SELECT * FROM {settings.fq_schema}.vw_sales_market_partgroup_trend WHERE upper(market_code)=:market_code ORDER BY sales_month DESC, revenue_eur DESC LIMIT 30", {"market_code": market_code})
    warranty = sql_client.query(f"""
        SELECT market_code, claim_month, SUM(total_claims) AS total_claims, SUM(rejected_claims) AS rejected_claims,
               ROUND(SUM(rejected_claims)/NULLIF(SUM(total_claims),0),4) AS rejection_rate
        FROM {settings.fq_schema}.vw_warranty_performance_summary
        WHERE upper(market_code)=:market_code
        GROUP BY market_code, claim_month
        ORDER BY claim_month DESC
        LIMIT 12
    """, {"market_code": market_code})
    return {"found": bool(sales or warranty), "entity_type": "market", "entity_id": market_code, "sales_trends": sales, "warranty_trends": warranty, "recommended_reasoning_focus": ["Analyze declining part groups.", "Compare revenue trend with warranty/service risk.", "Identify RCA candidates from growth and rejection signals."]}

def generate_aftermarket_context_pack_impl(entity_type: str, entity_id: str) -> dict:
    t = entity_type.strip().lower()
    eid = entity_id.strip().upper()
    if t == "dealer": return _dealer_context(eid)
    if t == "vin": return {"entity_type": "vin", "entity_id": eid, "service_history": get_vehicle_service_history_impl(eid), "recommended_reasoning_focus": ["Check repeat repair indicator.", "Review latest fault code and escalation status.", "Assess warranty implications if repeat issue exists."]}
    if t == "claim": return {"entity_type": "claim", "entity_id": eid, "warranty_claim": get_warranty_claim_details_impl(eid), "recommended_reasoning_focus": ["Explain rejection or status.", "Identify missing documents.", "Assess whether resubmission is possible."]}
    if t == "market": return _market_context(eid)
    if t == "part": return {"entity_type": "part", "entity_id": eid, "part_availability": check_part_availability_impl(eid), "recommended_reasoning_focus": ["Check availability and backorder risk.", "Look for alternate, reman, or end-of-chain options.", "Recommend escalation if critical part is unavailable."]}
    return {"found": False, "entity_type": entity_type, "entity_id": entity_id, "message": "Unsupported entity_type. Use: dealer, vin, claim, market, part."}
