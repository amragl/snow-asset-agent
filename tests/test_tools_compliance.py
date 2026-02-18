"""Tests for snow_asset_agent.tools.compliance."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.compliance import _safe_int, check_license_compliance
from tests.helpers import make_license_record, make_mock_response


class TestSafeInt:
    def test_valid(self):
        assert _safe_int("42") == 42

    def test_float_string(self):
        assert _safe_int("42.7") == 42

    def test_none(self):
        assert _safe_int(None) == 0

    def test_empty(self):
        assert _safe_int("") == 0

    def test_invalid(self):
        assert _safe_int("abc") == 0


class TestCheckLicenseCompliance:
    def test_compliant_license(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="100", allocated="60")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert result["count"] == 1
        assert result["compliance_results"][0]["status"] == "compliant"

    def test_over_allocated(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="50", allocated="80")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert result["compliance_results"][0]["status"] == "over-allocated"
        assert result["non_compliant"] == 1

    def test_under_utilised(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="100", allocated="20")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert result["compliance_results"][0]["status"] == "under-utilised"
        assert result["under_utilised"] == 1

    def test_zero_rights(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="0", allocated="0")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert result["compliance_results"][0]["status"] == "unknown"

    def test_gap_calculation(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record(rights="50", allocated="70")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert result["compliance_results"][0]["gap"] == 20

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = check_license_compliance(client=client)
        assert result["count"] == 0
        assert result["compliant"] == 0

    def test_product_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        check_license_compliance(client=client, product="Office")
        params = client._session.get.call_args[1].get("params", {})
        assert "Office" in str(params)

    def test_vendor_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        check_license_compliance(client=client, vendor="Adobe")
        params = client._session.get.call_args[1].get("params", {})
        assert "Adobe" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = check_license_compliance(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = check_license_compliance(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = check_license_compliance(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = check_license_compliance(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record()
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert "compliance_results" in result
        assert "count" in result
        assert "compliant" in result
        assert "non_compliant" in result
        assert "under_utilised" in result

    def test_result_item_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record()
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        item = result["compliance_results"][0]
        assert "sys_id" in item
        assert "rights" in item
        assert "allocated" in item
        assert "gap" in item
        assert "status" in item

    def test_multiple_licenses(self, client_with_mock_session):
        client = client_with_mock_session
        records = [
            make_license_record(sys_id="l1", rights="100", allocated="60"),
            make_license_record(sys_id="l2", rights="50", allocated="80"),
        ]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = check_license_compliance(client=client)
        assert result["count"] == 2
        assert result["compliant"] == 1
        assert result["non_compliant"] == 1

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = check_license_compliance(client=client)
        assert "error" in result

    def test_software_model_as_dict(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record()
        rec["software_model"] = {"display_value": "Photoshop", "value": "ps1"}
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        assert result["compliance_results"][0]["product"] == "Photoshop"

    def test_negative_limit(self, client_with_mock_session):
        result = check_license_compliance(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_missing_rights_field(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_license_record()
        rec.pop("rights")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = check_license_compliance(client=client)
        # rights defaults to 0 -> status should be "unknown"
        assert result["compliance_results"][0]["status"] == "unknown"
