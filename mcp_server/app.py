from __future__ import annotations
import inspect, os
from mcp.server.fastmcp import FastMCP
from config.settings import settings
from db.sql_client import sql_client
from tools.warranty_tools import get_warranty_claim_details_impl
from tools.service_tools import get_vehicle_service_history_impl
from tools.parts_tools import check_part_availability_impl
from tools.context_pack_tools import generate_aftermarket_context_pack_impl

mcp = FastMCP("Aftermarket Custom MCP Tools - Local")

@mcp.tool()
def health_check(include_sql_ping: bool = False) -> dict:
    result = {"status": "ok", "server": "Aftermarket Custom MCP Tools - Local", "catalog": settings.catalog, "schema": settings.schema, "transport": settings.mcp_transport, "host": settings.mcp_host, "port": settings.mcp_port}
    if include_sql_ping:
        result["databricks_sql"] = sql_client.ping()
    return result

@mcp.tool()
def get_warranty_claim_details(claim_id: str) -> dict:
    return get_warranty_claim_details_impl(claim_id)

@mcp.tool()
def get_vehicle_service_history(vin: str, limit: int = 10) -> dict:
    return get_vehicle_service_history_impl(vin, limit)

@mcp.tool()
def check_part_availability(part_number: str, market_code: str | None = None, limit: int = 10) -> dict:
    return check_part_availability_impl(part_number, market_code, limit)

@mcp.tool()
def generate_aftermarket_context_pack(entity_type: str, entity_id: str) -> dict:
    return generate_aftermarket_context_pack_impl(entity_type, entity_id)

def _run_mcp() -> None:
    if settings.mcp_transport == "stdio":
        mcp.run()
        return
    sig = inspect.signature(mcp.run)
    kwargs = {}
    if "transport" in sig.parameters: kwargs["transport"] = settings.mcp_transport
    if "host" in sig.parameters: kwargs["host"] = settings.mcp_host
    if "port" in sig.parameters: kwargs["port"] = settings.mcp_port
    if kwargs:
        mcp.run(**kwargs)
    else:
        os.environ["HOST"] = settings.mcp_host
        os.environ["PORT"] = str(settings.mcp_port)
        mcp.run()

if __name__ == "__main__":
    _run_mcp()
