# SNOW Asset Agent - ServiceNow Asset Management

## Overview
Asset lifecycle tracking, license compliance, hardware/software inventory, cost optimization, and depreciation analysis for ServiceNow Asset Management via REST API.

## Core Principles (NON-NEGOTIABLE)
1. **ZERO MOCKS** — Every API call, data point, and integration must be real. No mock data, no hardcoded values, no stub implementations. If the ServiceNow instance isn’t available, STOP and report the blocker.
2. **FAIL-STOP** — If any agent or tool encounters an error, the pipeline halts. No silent failures. No workarounds. Fix the issue, then resume.
3. **READ-HEAVY** — Most tools are read-only queries. Write operations (reconcile) require explicit confirmation.

## Architecture
```
FastMCP Server (server.py)
  |
  +-- get_hardware_assets       (hardware inventory)
  +-- get_software_licenses     (software license inventory)
  +-- get_asset_details         (single asset deep-dive)
  +-- get_asset_lifecycle       (lifecycle stage tracking)
  +-- get_asset_contracts       (contract associations)
  +-- get_asset_costs           (cost analysis)
  +-- check_license_compliance  (license compliance audit)
  +-- get_asset_utilization     (utilization metrics)
  +-- calculate_depreciation    (depreciation calculations)
  +-- find_underutilized        (underutilized asset detection)
  +-- reconcile_assets          (asset reconciliation)
  +-- get_asset_health          (overall asset health score)
  +-- get_expiring_contracts    (expiring contract alerts)
  +-- get_expiring_warranties   (expiring warranty alerts)
  |
  +-- ServiceNowClient (client.py) -> ServiceNow REST API
```

## MCP Tools (14 tools)
| Tool | Purpose |
|------|---------|
| `get_hardware_assets` | Query hardware asset inventory |
| `get_software_licenses` | Query software license inventory |
| `get_asset_details` | Deep-dive into single asset |
| `get_asset_lifecycle` | Track asset lifecycle stages |
| `get_asset_contracts` | View contract associations |
| `get_asset_costs` | Cost analysis and optimization |
| `check_license_compliance` | License compliance auditing |
| `get_asset_utilization` | Asset utilization metrics |
| `calculate_depreciation` | Depreciation calculations |
| `find_underutilized` | Detect underutilized assets |
| `reconcile_assets` | Asset reconciliation |
| `get_asset_health` | Overall asset health scoring |
| `get_expiring_contracts` | Expiring contract alerts |
| `get_expiring_warranties` | Expiring warranty alerts |

## ServiceNow Tables
| Table | Purpose |
|-------|---------|
| `alm_hardware` | Hardware assets |
| `alm_license` | Software licenses |
| `alm_asset` | Base asset table |
| `ast_contract` | Asset contracts |
| `cmdb_ci` | Configuration items |

## Configuration
- **Env prefix:** `SERVICENOW_*`
- **Key variables:** `SERVICENOW_INSTANCE`, `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD`

## Key Files
- `src/snow_asset_agent/server.py` — MCP server entry point
- `src/snow_asset_agent/tools/` — Tool modules
- `src/snow_asset_agent/client.py` — ServiceNow REST API client

## Git Workflow
- All agent work happens on feature branches
- PRs for human review before merging
- Never push directly to main
