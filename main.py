from fastmcp import FastMCP

from tools import get_related_queries_trends

mcp = FastMCP(name="Ultimate MCP")

@mcp.tool
async def related_query_trends(query: str) -> list:
    """Gets info about related queries popularity using google trends."""
    return await get_related_queries_trends(query)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9000)
