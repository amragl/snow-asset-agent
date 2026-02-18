"""Tests for snow_asset_agent.tools.contracts."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.contracts import _build_query, get_asset_contracts
from tests.helpers import make_contract_record, make_mock_response


class TestBuildQuery:
    def test_empty(self):
        assert _build_query() == ""

    def test_asset_sys_id(self):
        assert _build_query(asset_sys_id="a1") == "asset=a1"

    def test_vendor(self):
        assert _build_query(vendor="Dell") == "vendorLIKEDell"

    def test_state(self):
        assert _build_query(state="Active") == "state=Active"

    def test_combined(self):
        q = _build_query(asset_sys_id="a1", vendor="Dell", state="Active")
        assert "asset=a1" in q
        assert "vendorLIKEDell" in q
        assert "state=Active" in q


class TestGetAssetContracts:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_contract_record()]})
        result = get_asset_contracts(client=client)
        assert "contracts" in result
        assert result["count"] == 1

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = get_asset_contracts(client=client)
        assert result["contracts"] == []
        assert result["count"] == 0

    def test_vendor_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        get_asset_contracts(client=client, vendor="HP")
        params = client._session.get.call_args[1].get("params", {})
        assert "HP" in str(params)

    def test_state_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        get_asset_contracts(client=client, state="Expired")
        params = client._session.get.call_args[1].get("params", {})
        assert "Expired" in str(params)

    def test_asset_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        get_asset_contracts(client=client, asset_sys_id="asset1")
        params = client._session.get.call_args[1].get("params", {})
        assert "asset1" in str(params)

    def test_invalid_limit(self, client_with_mock_session):
        result = get_asset_contracts(client=client_with_mock_session, limit=0)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = get_asset_contracts(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = get_asset_contracts(client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = get_asset_contracts(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [make_contract_record()]})
        result = get_asset_contracts(client=client)
        c = result["contracts"][0]
        assert "sys_id" in c
        assert "contract_number" in c
        assert "vendor" in c

    def test_multiple_contracts(self, client_with_mock_session):
        client = client_with_mock_session
        records = [make_contract_record(sys_id=f"c{i}") for i in range(4)]
        client._session.get.return_value = make_mock_response(json_data={"result": records})
        result = get_asset_contracts(client=client)
        assert result["count"] == 4

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = get_asset_contracts(client=client)
        assert "error" in result

    def test_cost_parsed(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": [make_contract_record(cost="9999.99")]}
        )
        result = get_asset_contracts(client=client)
        assert result["contracts"][0]["cost"] == 9999.99

    def test_negative_limit(self, client_with_mock_session):
        result = get_asset_contracts(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_no_filters(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = get_asset_contracts(client=client)
        assert result["count"] == 0
