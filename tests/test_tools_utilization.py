"""Tests for snow_asset_agent.tools.utilization."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.utilization import _safe_int, get_license_utilization
from tests.helpers import make_license_record, make_mock_response


class TestSafeInt:
    def test_valid(self):
        assert _safe_int("42") == 42

    def test_none(self):
        assert _safe_int(None) == 0

    def test_empty(self):
        assert _safe_int("") == 0


class TestGetLicenseUtilization:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="100", allocated="85")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        assert "utilization" in result
        assert result["count"] == 1
        assert result["utilization"][0]["utilization_pct"] == 85.0

    def test_zero_rights(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="0", allocated="10")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        assert result["utilization"][0]["utilization_pct"] == 0.0

    def test_sorted_descending(self, client_with_mock_session):
        client = client_with_mock_session
        records = [
            make_license_record(sys_id="l1", rights="100", allocated="30"),
            make_license_record(sys_id="l2", rights="100", allocated="90"),
            make_license_record(sys_id="l3", rights="100", allocated="60"),
        ]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = get_license_utilization(client=client)
        pcts = [item["utilization_pct"] for item in result["utilization"]]
        assert pcts == sorted(pcts, reverse=True)

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = get_license_utilization(client=client)
        assert result["count"] == 0

    def test_product_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        get_license_utilization(client=client, product="Office")
        params = client._session.get.call_args[1].get("params", {})
        assert "Office" in str(params)

    def test_vendor_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        get_license_utilization(client=client, vendor="Microsoft")
        params = client._session.get.call_args[1].get("params", {})
        assert "Microsoft" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = get_license_utilization(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = get_license_utilization(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = get_license_utilization(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = get_license_utilization(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record()
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        item = result["utilization"][0]
        assert "sys_id" in item
        assert "product" in item
        assert "rights" in item
        assert "allocated" in item
        assert "utilization_pct" in item

    def test_utilization_calculation(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="200", allocated="50")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        assert result["utilization"][0]["utilization_pct"] == 25.0

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = get_license_utilization(client=client)
        assert "error" in result

    def test_software_model_as_dict(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record()
        rec["software_model"] = {"display_value": "AutoCAD", "value": "ac1"}
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        assert result["utilization"][0]["product"] == "AutoCAD"

    def test_negative_limit(self, client_with_mock_session):
        result = get_license_utilization(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_100_percent_utilization(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="50", allocated="50")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        assert result["utilization"][0]["utilization_pct"] == 100.0

    def test_over_100_percent(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="50", allocated="75")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = get_license_utilization(client=client)
        assert result["utilization"][0]["utilization_pct"] == 150.0
