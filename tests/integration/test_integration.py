"""Integration tests requiring a live ServiceNow instance.

These tests are skipped when SERVICENOW_INSTANCE is not set.
Run with: ``pytest -m integration`` after setting env vars.
"""

from __future__ import annotations

import os

import pytest

# Skip the entire module if ServiceNow credentials are not available.
pytestmark = pytest.mark.integration

SKIP_REASON = "SERVICENOW_INSTANCE not set; skipping integration tests"
skip_if_no_snow = pytest.mark.skipif(
    not os.environ.get("SERVICENOW_INSTANCE"),
    reason=SKIP_REASON,
)


@skip_if_no_snow
class TestHealthCheck:
    def test_health_check_connectivity(self):
        from snow_asset_agent.client import ServiceNowClient
        from snow_asset_agent.config import get_config

        client = ServiceNowClient(get_config())
        result = client.ping()
        assert result["status"] == "ok"
        assert result["response_time_s"] > 0


@skip_if_no_snow
class TestHardwareAssets:
    def test_query_returns_list(self):
        from snow_asset_agent.tools.hardware import query_hardware_assets

        result = query_hardware_assets(limit=5)
        assert "assets" in result
        assert isinstance(result["assets"], list)


@skip_if_no_snow
class TestSoftwareLicenses:
    def test_query_returns_list(self):
        from snow_asset_agent.tools.software import query_software_licenses

        result = query_software_licenses(limit=5)
        assert "licenses" in result
        assert isinstance(result["licenses"], list)


@skip_if_no_snow
class TestAssetContracts:
    def test_query_returns_list(self):
        from snow_asset_agent.tools.contracts import get_asset_contracts

        result = get_asset_contracts(limit=5)
        assert "contracts" in result


@skip_if_no_snow
class TestAssetHealthMetrics:
    def test_returns_metrics(self):
        from snow_asset_agent.tools.health import get_asset_health_metrics

        result = get_asset_health_metrics()
        assert "metrics" in result


@skip_if_no_snow
class TestLicenseCompliance:
    def test_returns_results(self):
        from snow_asset_agent.tools.compliance import check_license_compliance

        result = check_license_compliance(limit=5)
        assert "compliance_results" in result


@skip_if_no_snow
class TestLicenseUtilization:
    def test_returns_utilization(self):
        from snow_asset_agent.tools.utilization import get_license_utilization

        result = get_license_utilization(limit=5)
        assert "utilization" in result


@skip_if_no_snow
class TestReconciliation:
    def test_returns_reconciliation(self):
        from snow_asset_agent.tools.reconcile import reconcile_assets_to_cis

        result = reconcile_assets_to_cis(limit=10)
        assert "matched_count" in result


@skip_if_no_snow
class TestExpiringContracts:
    def test_returns_contracts(self):
        from snow_asset_agent.tools.expiring import find_expiring_contracts

        result = find_expiring_contracts(days_ahead=90)
        assert "contracts" in result
