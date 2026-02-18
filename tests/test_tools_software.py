"""Tests for snow_asset_agent.tools.software."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.software import _build_query, query_software_licenses
from tests.helpers import make_license_record, make_mock_response


class TestBuildQuery:
    def test_empty(self):
        assert _build_query() == ""

    def test_vendor(self):
        assert _build_query(vendor="Microsoft") == "vendorLIKEMicrosoft"

    def test_product(self):
        assert _build_query(product="Office") == "software_modelLIKEOffice"

    def test_expiring_soon(self):
        q = _build_query(expiring_soon=30)
        assert "end_date>=" in q
        assert "end_date<=" in q

    def test_combined(self):
        q = _build_query(vendor="Adobe", product="Photoshop")
        assert "vendorLIKEAdobe" in q
        assert "software_modelLIKEPhotoshop" in q


class TestQuerySoftwareLicenses:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_license_record()]})
        result = query_software_licenses(client=client)
        assert "licenses" in result
        assert result["count"] == 1

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = query_software_licenses(client=client)
        assert result["licenses"] == []
        assert result["count"] == 0

    def test_vendor_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_software_licenses(client=client, vendor="Microsoft")
        params = client._session.get.call_args[1].get("params", {})
        assert "Microsoft" in str(params)

    def test_product_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_software_licenses(client=client, product="Office")
        params = client._session.get.call_args[1].get("params", {})
        assert "Office" in str(params)

    def test_expiring_soon_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        query_software_licenses(client=client, expiring_soon=60)
        params = client._session.get.call_args[1].get("params", {})
        assert "end_date" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = query_software_licenses(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_negative_limit(self, client_with_mock_session):
        result = query_software_licenses(client=client_with_mock_session, limit=-5)
        assert "error" in result

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = query_software_licenses(client=client)
        assert "error" in result
        assert result["error_code"] == "SN_QUERY_ERROR"

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = query_software_licenses(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "server error"}}
        )
        result = query_software_licenses(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_license_record()]})
        result = query_software_licenses(client=client)
        assert "licenses" in result
        assert "count" in result
        lic = result["licenses"][0]
        assert "sys_id" in lic

    def test_rights_parsed_as_int(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_license_record(rights="200")]})
        result = query_software_licenses(client=client)
        assert result["licenses"][0]["rights"] == 200

    def test_multiple_results(self, client_with_mock_session):
        client = client_with_mock_session
        records = [make_license_record(sys_id=f"lic{i}") for i in range(3)]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = query_software_licenses(client=client)
        assert result["count"] == 3

    def test_timeout_returns_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = query_software_licenses(client=client)
        assert "error" in result

    def test_no_filters(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = query_software_licenses(client=client)
        assert result["count"] == 0
