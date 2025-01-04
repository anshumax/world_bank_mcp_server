import asyncio
import logging
import os
from mysql.connector import connect, Error
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl
import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mysql_mcp_server")

# Initialize server
app = Server("mysql_mcp_server")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List MySQL tables as resources."""
    try:
        resources = [
            Resource(
                uri=f"https://api.worldbank.org/v2/country?format=json&per_page=1000",
                name=f"Countries list",
                mimeType="application/json",
                description=f"List of countries in the World Bank database"
            ),
            Resource(
                uri=f"https://api.worldbank.org/v2/indicator?format=json&per_page=50000",
                name=f"Indicators list",
                mimeType="application/json",
                description=f"List of indicators in the World Bank database"
            )
        ]
        return resources
    except Error as e:
        logger.error(f"Failed to list resources: {str(e)}")
        return []

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read table contents."""
    uri_str = str(uri)
    logger.info(f"Reading resource: {uri_str}")
    
    try:
        response = requests.get(uri_str)
        indicator_values = response.json()[1]
        return pd.json_normalize(indicator_values).to_csv()
                
    except Error as e:
        logger.error(f"Database error reading resource {uri}: {str(e)}")
        raise RuntimeError(f"Database error: {str(e)}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available World Bank tools."""
    logger.info("Listing tools...")
    return [
        Tool(
            name="get_indicator_for_country",
            description="Get values for an indicator for a specific country from the World Bank API",
            inputSchema={
                "type": "object",
                "properties": {
                    "country_id": {
                        "type": "string",
                        "description": "The ID of the country for which the indicator is to be queried"
                    },
                    "indicator_id": {
                        "type": "string",
                        "description": "The ID of the indicator to be queried"
                    }
                },
                "required": ["country_id","indicator_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Get Indicator data."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")
    
    if name != "get_indicator_for_country":
        raise ValueError(f"Unknown tool: {name}")
    
    country_id = arguments.get("country_id")
    if not country_id:
        raise ValueError("country_id is required")

    indicator_id = arguments.get("indicator_id")
    if not indicator_id:
        raise ValueError("indicator_id is required")

    request_url = f"https://api.worldbank.org/v2/country/{country_id}/indicator/{indicator_id}?format=json&per_page=20000"
    try:
        response = requests.get(request_url)
        indicator_values = response.json()[1]
        return [TextContent(type="text", text=pd.json_normalize(indicator_values).to_csv())]
                
    except Error as e:
        logger.error(f"Error reading data from '{request_url}': {e}")
        return [TextContent(type="text", text=f"Error getting data from '{request_url}': {str(e)}")]

async def main():
    """Main entry point to run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting World Bank MCP server...")
    
    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    asyncio.run(main())