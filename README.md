# World Bank MCP Server

A Model Context Protocol (MCP) server that enables interaction with the open World Bank data API. This server allows AI assistants to list indicators and analyse those indicators for the countries that are available with the World Bank.

## Features

- List available countries in the World Bank open data API
- List available indicators in the World Bank open data API
- Analyse indicators, such as population segments, poverty numbers etc, for countries
- Comprehensive logging


## Usage

### With Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "world_bank": {
      "command": "uv",
      "args": [
        "--directory", 
        "path/to/world_bank_mcp_server",
        "run",
        "world_bank_mcp_server"
      ]
    }
  }
}
```
