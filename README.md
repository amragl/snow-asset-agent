# Snow Asset Agent

MCP server for ServiceNow Asset Management -- lifecycle tracking, license compliance, hardware/software inventory, and cost optimization.

## Architecture

```
Claude Desktop / Claude Code
        |
        | MCP (stdio)
        v
+-------------------+
| snow-asset-agent  |
| (FastMCP server)  |
+-------------------+
| 14 MCP tools      |
| config.py         |
| client.py         |
| models.py         |
| exceptions.py     |
+-------------------+
        |
        | HTTPS / REST
        v
+-------------------+
| ServiceNow        |
| Table API         |
| alm_hardware      |
| alm_license       |
| alm_asset         |
| ast_contract      |
| cmdb_ci           |
+-------------------+
```

## Prerequisites

- Python 3.11+
- A ServiceNow instance with asset tables
- A ServiceNow user with the `asset` or `itil` role (read access to `alm_*`, `ast_contract`, `cmdb_ci`)

## Installation

```bash
# From source
git clone https://github.com/amragl/snow-asset-agent.git
cd snow-asset-agent
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and fill in your ServiceNow credentials:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICENOW_INSTANCE` | Yes | -- | Full URL, e.g. `https://dev12345.service-now.com` |
| `SERVICENOW_USERNAME` | Yes | -- | ServiceNow username |
| `SERVICENOW_PASSWORD` | Yes | -- | ServiceNow password |
| `SERVICENOW_TIMEOUT` | No | `30` | HTTP timeout in seconds |
| `SERVICENOW_MAX_RETRIES` | No | `3` | Retry count for transient errors |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Quick Start

### Claude Code

Add to your MCP config:

```json
{
  "mcpServers": {
    "snow-asset-agent": {
      "command": "python",
      "args": ["-m", "snow_asset_agent"],
      "cwd": "/path/to/snow-asset-agent",
      "env": {
        "SERVICENOW_INSTANCE": "https://your-instance.service-now.com",
        "SERVICENOW_USERNAME": "your-user",
        "SERVICENOW_PASSWORD": "your-pass"
      }
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "snow-asset-agent": {
      "command": "python",
      "args": ["-m", "snow_asset_agent"],
      "cwd": "/path/to/snow-asset-agent"
    }
  }
}
```

### Docker

```bash
docker compose up -d
```

## MCP Tool Reference

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `health_check` | Verify ServiceNow connectivity | -- |
| `tool_query_hardware_assets` | Search hardware assets | `status`, `department`, `model`, `limit` |
| `tool_query_software_licenses` | Search software licenses | `vendor`, `product`, `expiring_soon`, `limit` |
| `tool_get_asset_details` | Full asset record by ID or tag | `sys_id`, `asset_tag` |
| `tool_get_asset_lifecycle` | Lifecycle stage and duration | `sys_id`, `asset_tag` |
| `tool_get_asset_contracts` | Contracts for an asset | `asset_sys_id`, `vendor`, `state`, `limit` |
| `tool_calculate_asset_costs` | Total cost of ownership | `department`, `model_category`, `limit` |
| `tool_check_license_compliance` | License vs. installed count | `product`, `vendor`, `limit` |
| `tool_get_license_utilization` | Used/total seats per product | `product`, `vendor`, `limit` |
| `tool_track_asset_depreciation` | Straight-line depreciation | `model_category`, `useful_life_years`, `limit` |
| `tool_find_underutilized_assets` | Inactive or unassigned assets | `days_threshold`, `limit` |
| `tool_reconcile_assets_to_cis` | Compare assets to CMDB CIs | `model_category`, `limit` |
| `tool_get_asset_health_metrics` | Aggregate health dashboard | `location`, `model_category` |
| `tool_find_expiring_contracts` | Contracts expiring soon | `days_ahead`, `vendor`, `include_expired`, `limit` |

## ServiceNow Tables

| Table | Description | Required Role |
|-------|-------------|---------------|
| `alm_hardware` | Hardware assets | `asset` |
| `alm_license` | Software licenses | `asset` |
| `alm_asset` | Base asset table | `asset` |
| `ast_contract` | Asset contracts | `asset` |
| `cmdb_ci` | Configuration items | `itil` |
| `sys_properties` | System properties (health check) | `admin` or `itil` |

## Project Structure

```
src/snow_asset_agent/
  __init__.py           Public exports + version
  __main__.py           Entry point
  config.py             Pydantic settings
  client.py             ServiceNow REST client
  exceptions.py         Exception hierarchy
  models.py             Pydantic models
  server.py             FastMCP server + tool registration
  py.typed              PEP 561 marker
  tools/
    __init__.py
    hardware.py         query_hardware_assets
    software.py         query_software_licenses
    details.py          get_asset_details
    lifecycle.py        get_asset_lifecycle
    contracts.py        get_asset_contracts
    costs.py            calculate_asset_costs
    compliance.py       check_license_compliance
    utilization.py      get_license_utilization
    depreciation.py     track_asset_depreciation
    underutilized.py    find_underutilized_assets
    reconcile.py        reconcile_assets_to_cis
    health.py           get_asset_health_metrics
    expiring.py         find_expiring_contracts
tests/
  conftest.py           Shared fixtures
  test_config.py
  test_exceptions.py
  test_models.py
  test_client.py
  test_server.py
  test_tools_*.py       One file per tool
  integration/
    test_integration.py
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/ --ignore=tests/integration -q

# Run with coverage
pytest tests/ --ignore=tests/integration --cov=snow_asset_agent --cov-report=term-missing

# Run integration tests (requires ServiceNow credentials)
pytest tests/integration -m integration

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/snow_asset_agent/
```

## License

MIT
