"""Tests for snow_asset_agent.tools.details."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.details import get_asset_details
from tests.helpers import make_hardware_record, make_mock_response


class TestGetAssetDetails:
    def test_by_sys_id(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": make_hardware_record()})
        result = get_asset_details(sys_id="abc123", client=client)
        assert "asset" in result
        assert result["asset"]["sys_id"] == "abc123"

    def test_by_asset_tag(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": [make_hardware_record(asset_tag="TAG999")]}
        )
        result = get_asset_details(asset_tag="TAG999", client=client)
        assert result["asset"]["asset_tag"] == "TAG999"

    def test_no_id_provided(self, client_with_mock_session):
        result = get_asset_details(client=client_with_mock_session)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_asset_not_found_by_tag(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = get_asset_details(asset_tag="MISSING", client=client)
        assert "error" in result
        assert result["error_code"] == "SN_NOT_FOUND"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = get_asset_details(sys_id="abc", client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = get_asset_details(sys_id="abc", client=client)
        assert "error" in result

    def test_500_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        result = get_asset_details(sys_id="abc", client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": make_hardware_record()})
        result = get_asset_details(sys_id="abc123", client=client)
        asset = result["asset"]
        assert "sys_id" in asset
        assert "display_name" in asset

    def test_404_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=404, ok=False, json_data={"error": {"message": "not found"}}
        )
        result = get_asset_details(sys_id="badid", client=client)
        assert "error" in result

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = get_asset_details(sys_id="abc", client=client)
        assert "error" in result

    def test_empty_sys_id_and_empty_tag(self, client_with_mock_session):
        result = get_asset_details(sys_id="", asset_tag="", client=client_with_mock_session)
        assert "error" in result
        assert result["error_code"] == "SN_VALIDATION_ERROR"

    def test_cost_parsed(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": make_hardware_record(cost="3500")})
        result = get_asset_details(sys_id="abc123", client=client)
        assert result["asset"]["cost"] == 3500.0

    def test_purchase_date_parsed(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            json_data={"result": make_hardware_record(purchase_date="2024-03-15")}
        )
        result = get_asset_details(sys_id="abc123", client=client)
        assert result["asset"]["purchase_date"] == "2024-03-15"

    def test_sys_id_preferred_over_tag(self, client_with_mock_session):
        """When both are provided, sys_id is used."""
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": make_hardware_record()})
        get_asset_details(sys_id="abc123", asset_tag="TAG", client=client)
        # Should use get_record (single) not get_records
        url = client._session.get.call_args[0][0]
        assert "abc123" in url

    def test_both_none(self, client_with_mock_session):
        result = get_asset_details(sys_id=None, asset_tag=None, client=client_with_mock_session)
        assert "error" in result
