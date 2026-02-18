"""Tests for snow_asset_agent.tools.hardware."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.hardware import _build_query, query_hardware_assets
from tests.helpers import make_hardware_record, make_mock_response


class TestBuildQuery:
    def test_empty(self):
        assert _build_query() == ""

    def test_status_only(self):
        assert _build_query(status="In use") == "install_status=In use"

    def test_department_only(self):
        assert _build_query(department="IT") == "department=IT"

    def test_model_only(self):
        assert _build_query(model="Dell") == "modelLIKEDell"

    def test_model_category(self):
        assert _build_query(model_category="Computer") == "model_category=Computer"

    def test_assigned_to(self):
        assert _build_query(assigned_to="John") == "assigned_toLIKEJohn"

    def test_location(self):
        assert _build_query(location="NYC") == "locationLIKENYC"

    def test_combined(self):
        q = _build_query(status="In use", department="IT")
        assert "install_status=In use" in q
        assert "department=IT" in q
        assert "^" in q


class TestQueryHardwareAssets:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_hardware_record()]})
        result = query_hardware_assets(client=client)
        assert "assets" in result
        assert result["count"] == 1
        assert result["assets"][0]["sys_id"] == "abc123"

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = query_hardware_assets(client=client)
        assert result["assets"] == []
        assert result["count"] == 0

    def test_multiple_results(self, client_with_mock_session):
        client = client_with_mock_session
        records = [make_hardware_record(sys_id=f"hw{i}") for i in range(5)]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = query_hardware_assets(client=client, limit=10)
        assert result["count"] == 5

    def test_status_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_hardware_assets(client=client, status="Retired")
        params = client._session.get.call_args[1].get("params", {})
        assert "Retired" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = query_hardware_assets(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_negative_limit(self, client_with_mock_session):
        result = query_hardware_assets(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = query_hardware_assets(client=client)
        assert "error" in result
        assert result["error_code"] == "SN_QUERY_ERROR"

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = query_hardware_assets(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = query_hardware_assets(client=client)
        assert "error" in result

    def test_output_has_required_keys(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_hardware_record()]})
        result = query_hardware_assets(client=client)
        assert "assets" in result
        assert "count" in result
        asset = result["assets"][0]
        assert "sys_id" in asset
        assert "asset_tag" in asset

    def test_department_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_hardware_assets(client=client, department="Finance")
        params = client._session.get.call_args[1].get("params", {})
        assert "Finance" in str(params)

    def test_model_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_hardware_assets(client=client, model="Latitude")
        params = client._session.get.call_args[1].get("params", {})
        assert "Latitude" in str(params)

    def test_location_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_hardware_assets(client=client, location="Chicago")
        params = client._session.get.call_args[1].get("params", {})
        assert "Chicago" in str(params)

    def test_cost_is_float(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": [make_hardware_record(cost="2500.50")]}
        )
        result = query_hardware_assets(client=client)
        assert result["assets"][0]["cost"] == 2500.50

    def test_missing_cost_is_none(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record()
        rec.pop("cost")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = query_hardware_assets(client=client)
        assert result["assets"][0]["cost"] is None

    def test_no_filters(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = query_hardware_assets(client=client)
        assert result["count"] == 0

    def test_all_filters(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_hardware_assets(
            client=client,
            status="In use",
            department="IT",
            model="Dell",
            model_category="Computer",
            assigned_to="John",
            location="NYC",
        )
        params = client._session.get.call_args[1].get("params", {})
        query_str = str(params)
        assert "In use" in query_str
        assert "IT" in query_str
        assert "Dell" in query_str

    def test_timeout_returns_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = query_hardware_assets(client=client)
        assert "error" in result
