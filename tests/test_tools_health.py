"""Tests for snow_asset_agent.tools.health."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.health import _safe_float, get_asset_health_metrics
from tests.helpers import make_contract_record, make_hardware_record, make_mock_response


class TestSafeFloat:
    def test_valid(self):
        assert _safe_float("100") == 100.0

    def test_none(self):
        assert _safe_float(None) == 0.0


class TestGetAssetHealthMetrics:
    def _make_asset(self, status, cost="1000"):
        rec = make_hardware_record(install_status=status, cost=cost)
        return rec

    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        assets = [
            self._make_asset("In use"),
            self._make_asset("Retired"),
            self._make_asset("Missing"),
            self._make_asset("In stock"),
        ]
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": assets}),
            make_mock_response(json_data={"result": []}),  # contracts
        ]
        result = get_asset_health_metrics(client=client)
        assert "metrics" in result
        m = result["metrics"]
        assert m["total_assets"] == 4
        assert m["active_assets"] == 1
        assert m["retired_assets"] == 1
        assert m["missing_assets"] == 1
        assert m["in_stock_assets"] == 1

    def test_empty_assets(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        result = get_asset_health_metrics(client=client)
        assert result["metrics"]["total_assets"] == 0

    def test_total_value(self, client_with_mock_session):
        client = client_with_mock_session
        assets = [self._make_asset("In use", "5000"), self._make_asset("In use", "3000")]
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": assets}),
            make_mock_response(json_data={"result": []}),
        ]
        result = get_asset_health_metrics(client=client)
        assert result["metrics"]["total_asset_value"] == 8000.0

    def test_expiring_contracts(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": [make_contract_record(), make_contract_record()]}),
        ]
        result = get_asset_health_metrics(client=client)
        assert result["metrics"]["expiring_contracts_30d"] == 2

    def test_location_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        get_asset_health_metrics(client=client, location="NYC")
        params = client._session.get.call_args_list[0][1].get("params", {})
        assert "NYC" in str(params)

    def test_model_category_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        get_asset_health_metrics(client=client, model_category="Server")
        params = client._session.get.call_args_list[0][1].get("params", {})
        assert "Server" in str(params)

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = get_asset_health_metrics(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = get_asset_health_metrics(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = get_asset_health_metrics(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        result = get_asset_health_metrics(client=client)
        m = result["metrics"]
        for key in [
            "total_assets",
            "active_assets",
            "retired_assets",
            "missing_assets",
            "in_stock_assets",
            "expiring_contracts_30d",
            "total_asset_value",
        ]:
            assert key in m

    def test_installed_counted_as_active(self, client_with_mock_session):
        client = client_with_mock_session
        assets = [self._make_asset("Installed")]
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": assets}),
            make_mock_response(json_data={"result": []}),
        ]
        result = get_asset_health_metrics(client=client)
        assert result["metrics"]["active_assets"] == 1

    def test_unknown_status(self, client_with_mock_session):
        client = client_with_mock_session
        assets = [self._make_asset("Custom Status")]
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": assets}),
            make_mock_response(json_data={"result": []}),
        ]
        result = get_asset_health_metrics(client=client)
        # Should still count total but not any specific category
        assert result["metrics"]["total_assets"] == 1
        assert result["metrics"]["active_assets"] == 0

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = get_asset_health_metrics(client=client)
        assert "error" in result

    def test_missing_cost_field(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        rec.pop("cost")
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [rec]}),
            make_mock_response(json_data={"result": []}),
        ]
        result = get_asset_health_metrics(client=client)
        # Should not crash, value treated as 0
        assert result["metrics"]["total_asset_value"] == 0.0
