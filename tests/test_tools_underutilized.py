"""Tests for snow_asset_agent.tools.underutilized."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.underutilized import _safe_float, find_underutilized_assets
from tests.helpers import make_hardware_record, make_mock_response


class TestSafeFloat:
    def test_valid(self):
        assert _safe_float("100") == 100.0

    def test_none(self):
        assert _safe_float(None) == 0.0

    def test_empty(self):
        assert _safe_float("") == 0.0


class TestFindUnderutilizedAssets:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(sys_updated_on="2020-01-01 00:00:00")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        assert "underutilized_assets" in result
        assert result["count"] == 1

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = find_underutilized_assets(client=client)
        assert result["count"] == 0

    def test_unassigned_reason(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(assigned_to="", sys_updated_on="2020-01-01 00:00:00")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        assert result["underutilized_assets"][0]["reason"] == "unassigned"

    def test_inactive_reason(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(assigned_to="John", sys_updated_on="2020-01-01 00:00:00")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        assert result["underutilized_assets"][0]["reason"] == "inactive"

    def test_waste_cost(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="2000")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        assert result["estimated_waste_cost"] == 2000.0

    def test_custom_threshold(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        find_underutilized_assets(client=client, days_threshold=30)
        params = client._session.get.call_args[1].get("params", {})
        assert "sys_updated_on" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = find_underutilized_assets(client=client_with_mock_session, limit=0)
        assert "error" in result

    def test_invalid_threshold(self, client_with_mock_session):
        result = find_underutilized_assets(client=client_with_mock_session, days_threshold=0)
        assert "error" in result

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = find_underutilized_assets(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = find_underutilized_assets(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = find_underutilized_assets(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        assert "underutilized_assets" in result
        assert "count" in result
        assert "estimated_waste_cost" in result

    def test_asset_item_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        item = result["underutilized_assets"][0]
        for key in ["sys_id", "asset_tag", "display_name", "reason", "cost"]:
            assert key in item

    def test_multiple_assets(self, client_with_mock_session):
        client = client_with_mock_session
        records = [make_hardware_record(sys_id=f"a{i}", cost=f"{i * 1000}") for i in range(1, 4)]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = find_underutilized_assets(client=client)
        assert result["count"] == 3
        assert result["estimated_waste_cost"] == 6000.0

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = find_underutilized_assets(client=client)
        assert "error" in result

    def test_negative_limit(self, client_with_mock_session):
        result = find_underutilized_assets(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_negative_threshold(self, client_with_mock_session):
        result = find_underutilized_assets(client=client_with_mock_session, days_threshold=-1)
        assert "error" in result

    def test_missing_cost(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        rec.pop("cost")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_underutilized_assets(client=client)
        assert result["underutilized_assets"][0]["cost"] == 0.0
