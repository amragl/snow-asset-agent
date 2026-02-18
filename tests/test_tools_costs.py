"""Tests for snow_asset_agent.tools.costs."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.costs import _safe_float, calculate_asset_costs
from tests.helpers import make_hardware_record, make_mock_response


class TestSafeFloat:
    def test_valid(self):
        assert _safe_float("100.50") == 100.50

    def test_none(self):
        assert _safe_float(None) == 0.0

    def test_empty(self):
        assert _safe_float("") == 0.0

    def test_invalid(self):
        assert _safe_float("abc") == 0.0

    def test_int_string(self):
        assert _safe_float("42") == 42.0


class TestCalculateAssetCosts:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": [make_hardware_record(cost="1000.00")]}
        )
        result = calculate_asset_costs(client=client)
        assert "total_purchase_cost" in result
        assert result["total_purchase_cost"] == 1000.0
        assert result["asset_count"] == 1

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = calculate_asset_costs(client=client)
        assert result["total_purchase_cost"] == 0.0
        assert result["asset_count"] == 0

    def test_multiple_assets(self, client_with_mock_session):
        client = client_with_mock_session
        records = [
            make_hardware_record(sys_id="a1", cost="1000"),
            make_hardware_record(sys_id="a2", cost="2000"),
        ]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = calculate_asset_costs(client=client)
        assert result["total_purchase_cost"] == 3000.0
        assert result["asset_count"] == 2

    def test_maintenance_calculation(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_hardware_record(cost="1000")]})
        result = calculate_asset_costs(client=client)
        # Maintenance = 15% of purchase
        assert result["total_annual_maintenance"] == 150.0

    def test_tco_calculation(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_hardware_record(cost="1000")]})
        result = calculate_asset_costs(client=client)
        # TCO = purchase + maintenance = 1000 + 150
        assert result["total_tco"] == 1150.0

    def test_department_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        calculate_asset_costs(client=client, department="IT")
        params = client._session.get.call_args[1].get("params", {})
        assert "IT" in str(params)

    def test_model_category_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        calculate_asset_costs(client=client, model_category="Server")
        params = client._session.get.call_args[1].get("params", {})
        assert "Server" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = calculate_asset_costs(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = calculate_asset_costs(client=client)
        assert "error" in result

    def test_zero_cost_assets(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_hardware_record(cost="0")]})
        result = calculate_asset_costs(client=client)
        assert result["total_purchase_cost"] == 0.0
        assert result["total_annual_maintenance"] == 0.0

    def test_missing_cost_field(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        rec.pop("cost")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = calculate_asset_costs(client=client)
        assert result["total_purchase_cost"] == 0.0

    def test_per_asset_breakdown(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_hardware_record(cost="2000")]})
        result = calculate_asset_costs(client=client)
        asset = result["assets"][0]
        assert "sys_id" in asset
        assert "purchase_cost" in asset
        assert "annual_maintenance" in asset
        assert "tco" in asset

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = calculate_asset_costs(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = calculate_asset_costs(client=client)
        assert "error" in result

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = calculate_asset_costs(client=client)
        assert "error" in result

    def test_negative_limit(self, client_with_mock_session):
        result = calculate_asset_costs(client=client_with_mock_session, limit=-1)
        assert "error" in result
