import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def main():
    server_params = StdioServerParameters(command="python", args=["app.py"], env={"MCP_TRANSPORT": "stdio"})
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("\nAvailable MCP tools:")
            for tool in tools.tools:
                print("-", tool.name)
            print("\nCalling health_check...")
            print(await session.call_tool("health_check", arguments={"include_sql_ping": False}))
            print("\nCalling get_warranty_claim_details...")
            print(await session.call_tool("get_warranty_claim_details", arguments={"claim_id": "WC1001"}))

if __name__ == "__main__":
    asyncio.run(main())
