"""Tests for snow_asset_agent.tools.expiring."""

from __future__ import annotations

from datetime import date, timedelta

import requests

from snow_asset_agent.tools.expiring import _urgency, find_expiring_contracts
from tests.helpers import make_contract_record, make_mock_response


class TestUrgency:
    def test_expired(self):
        assert _urgency(-5) == "expired"

    def test_critical(self):
        assert _urgency(15) == "critical"

    def test_warning(self):
        assert _urgency(45) == "warning"

    def test_notice(self):
        assert _urgency(75) == "notice"

    def test_info(self):
        assert _urgency(120) == "info"

    def test_boundary_30(self):
        assert _urgency(30) == "critical"

    def test_boundary_60(self):
        assert _urgency(60) == "warning"

    def test_boundary_90(self):
        assert _urgency(90) == "notice"

    def test_zero(self):
        assert _urgency(0) == "critical"


class TestFindExpiringContracts:
    def _make_expiring_contract(self, days_from_now=30):
        end_date = (date.today() + timedelta(days=days_from_now)).isoformat()
        return make_contract_record(ends=end_date)

    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        rec = self._make_expiring_contract(15)
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_expiring_contracts(client=client)
        assert "contracts" in result
        assert result["count"] == 1

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = find_expiring_contracts(client=client)
        assert result["count"] == 0

    def test_days_remaining_calculated(self, client_with_mock_session):
        client = client_with_mock_session
        rec = self._make_expiring_contract(20)
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_expiring_contracts(client=client)
        c = result["contracts"][0]
        assert c["days_remaining"] == 20

    def test_urgency_assigned(self, client_with_mock_session):
        client = client_with_mock_session
        rec = self._make_expiring_contract(15)
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_expiring_contracts(client=client)
        assert result["contracts"][0]["urgency"] == "critical"

    def test_sorted_by_days_remaining(self, client_with_mock_session):
        client = client_with_mock_session
        records = [
            self._make_expiring_contract(60),
            self._make_expiring_contract(10),
            self._make_expiring_contract(30),
        ]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = find_expiring_contracts(client=client)
        days = [c["days_remaining"] for c in result["contracts"]]
        assert days == sorted(days)

    def test_total_value_at_risk(self, client_with_mock_session):
        client = client_with_mock_session
        rec = self._make_expiring_contract(30)
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_expiring_contracts(client=client)
        assert result["total_value_at_risk"] == 5000.0

    def test_vendor_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        find_expiring_contracts(client=client, vendor="Dell")
        params = client._session.get.call_args[1].get("params", {})
        assert "Dell" in str(params)

    def test_include_expired(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        find_expiring_contracts(client=client, include_expired=True)
        params = client._session.get.call_args[1].get("params", {})
        # Should include dates in the past
        query = str(params)
        assert "ends>=" in query

    def test_custom_days_ahead(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        find_expiring_contracts(client=client, days_ahead=180)
        params = client._session.get.call_args[1].get("params", {})
        future_date = (date.today() + timedelta(days=180)).isoformat()
        assert future_date in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = find_expiring_contracts(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_invalid_days_ahead(self, client_with_mock_session):
        result = find_expiring_contracts(client=client_with_mock_session, days_ahead=0)
        assert "error" in result

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = find_expiring_contracts(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = find_expiring_contracts(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = find_expiring_contracts(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = self._make_expiring_contract(30)
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_expiring_contracts(client=client)
        assert "contracts" in result
        assert "count" in result
        assert "total_value_at_risk" in result
        c = result["contracts"][0]
        assert "days_remaining" in c
        assert "urgency" in c

    def test_contract_without_ends(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_contract_record()
        rec.pop("ends")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = find_expiring_contracts(client=client)
        c = result["contracts"][0]
        assert c["days_remaining"] is None
        assert c["urgency"] == "unknown"

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = find_expiring_contracts(client=client)
        assert "error" in result

    def test_negative_limit(self, client_with_mock_session):
        result = find_expiring_contracts(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_negative_days_ahead(self, client_with_mock_session):
        result = find_expiring_contracts(client=client_with_mock_session, days_ahead=-1)
        assert "error" in result

    def test_multiple_contracts(self, client_with_mock_session):
        client = client_with_mock_session
        records = [
            self._make_expiring_contract(10),
            self._make_expiring_contract(50),
        ]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = find_expiring_contracts(client=client)
        assert result["count"] == 2
