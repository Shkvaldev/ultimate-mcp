from fastmcp import FastMCP

from tools import get_related_queries_trends

mcp = FastMCP(name="Ultimate MCP")

@mcp.tool
async def related_query_trends(query: str) -> dict:
    """Gets info about related queries popularity using google trends."""
    data = await get_related_queries_trends(query)
    if not data:
        return {"error": "failed to get related query trends"}
    return data

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9000)
