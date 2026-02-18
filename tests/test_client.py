"""Tests for snow_asset_agent.client.

Uses MagicMock to simulate HTTP responses from the ``requests`` library.
This is the only acceptable use of mocking per project policy.
"""

from __future__ import annotations

import pytest
import requests

from snow_asset_agent.client import ServiceNowClient
from snow_asset_agent.exceptions import (
    ServiceNowAPIError,
    ServiceNowAuthError,
    ServiceNowConnectionError,
    ServiceNowNotFoundError,
    ServiceNowPermissionError,
    ServiceNowRateLimitError,
)
from tests.helpers import make_mock_response

# ------------------------------------------------------------------
# Client initialisation
# ------------------------------------------------------------------


class TestClientInit:
    def test_base_url(self, test_config, mock_session):
        client = ServiceNowClient(test_config)
        assert client._base_url == "https://test.service-now.com/api/now"

    def test_session_created(self, test_config, mock_session):
        client = ServiceNowClient(test_config)
        # Session should exist
        assert client._session is not None


# ------------------------------------------------------------------
# get_records
# ------------------------------------------------------------------


class TestGetRecords:
    def test_returns_result_list(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [{"sys_id": "1"}, {"sys_id": "2"}]})
        records = client.get_records("alm_hardware")
        assert len(records) == 2
        assert records[0]["sys_id"] == "1"

    def test_empty_result(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        records = client.get_records("alm_hardware")
        assert records == []

    def test_query_param(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        client.get_records("alm_hardware", query="install_status=In use", limit=10)
        _, kwargs = client._session.get.call_args
        assert "install_status=In use" in str(kwargs.get("params", {}))

    def test_fields_param(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        client.get_records("alm_hardware", fields=["sys_id", "asset_tag"])
        _, kwargs = client._session.get.call_args
        assert "sys_id,asset_tag" in str(kwargs.get("params", {}))

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("refused")
        with pytest.raises(ServiceNowConnectionError):
            client.get_records("alm_hardware")

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        with pytest.raises(ServiceNowConnectionError):
            client.get_records("alm_hardware")

    def test_401_raises_auth_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "bad creds"}}
        )
        with pytest.raises(ServiceNowAuthError):
            client.get_records("alm_hardware")

    def test_403_raises_permission_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=403, ok=False, json_data={"error": {"message": "forbidden"}}
        )
        with pytest.raises(ServiceNowPermissionError):
            client.get_records("alm_hardware")

    def test_404_raises_not_found(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=404, ok=False, json_data={"error": {"message": "not found"}}
        )
        with pytest.raises(ServiceNowNotFoundError):
            client.get_records("alm_hardware")

    def test_429_raises_rate_limit(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=429, ok=False, json_data={"error": {"message": "rate limited"}}
        )
        with pytest.raises(ServiceNowRateLimitError):
            client.get_records("alm_hardware")

    def test_500_raises_api_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=500, ok=False, json_data={"error": {"message": "internal"}}
        )
        with pytest.raises(ServiceNowAPIError):
            client.get_records("alm_hardware")

    def test_non_json_error_body(self, client_with_mock_session):
        client = client_with_mock_session
        resp = make_mock_response(status_code=502, ok=False, text="Bad Gateway")
        resp.json.side_effect = ValueError("no json")
        client._session.get.return_value = resp
        with pytest.raises(ServiceNowAPIError):
            client.get_records("alm_hardware")


# ------------------------------------------------------------------
# get_record
# ------------------------------------------------------------------


class TestGetRecord:
    def test_returns_single_dict(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": {"sys_id": "abc"}})
        record = client.get_record("alm_hardware", "abc")
        assert record["sys_id"] == "abc"

    def test_not_found(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=404, ok=False, json_data={"error": {"message": "not found"}}
        )
        with pytest.raises(ServiceNowNotFoundError):
            client.get_record("alm_hardware", "badid")

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.get_record("alm_hardware", "abc")

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.get_record("alm_hardware", "abc")


# ------------------------------------------------------------------
# create_record
# ------------------------------------------------------------------


class TestCreateRecord:
    def test_success(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.post.return_value = make_mock_response(json_data={"result": {"sys_id": "new1"}})
        result = client.create_record("alm_hardware", {"asset_tag": "NEW"})
        assert result["sys_id"] == "new1"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.post.side_effect = requests.ConnectionError("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.create_record("alm_hardware", {})

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.post.side_effect = requests.Timeout("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.create_record("alm_hardware", {})


# ------------------------------------------------------------------
# update_record
# ------------------------------------------------------------------


class TestUpdateRecord:
    def test_success(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.patch.return_value = make_mock_response(
            json_data={"result": {"sys_id": "u1", "asset_tag": "UPDATED"}}
        )
        result = client.update_record("alm_hardware", "u1", {"asset_tag": "UPDATED"})
        assert result["asset_tag"] == "UPDATED"

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.patch.side_effect = requests.ConnectionError("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.update_record("alm_hardware", "u1", {})

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.patch.side_effect = requests.Timeout("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.update_record("alm_hardware", "u1", {})


# ------------------------------------------------------------------
# delete_record
# ------------------------------------------------------------------


class TestDeleteRecord:
    def test_success(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.delete.return_value = make_mock_response(status_code=204)
        assert client.delete_record("alm_hardware", "d1") is True

    def test_not_found(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.delete.return_value = make_mock_response(
            status_code=404, ok=False, json_data={"error": {"message": "not found"}}
        )
        with pytest.raises(ServiceNowNotFoundError):
            client.delete_record("alm_hardware", "bad")

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.delete.side_effect = requests.ConnectionError("fail")
        with pytest.raises(ServiceNowConnectionError):
            client.delete_record("alm_hardware", "d1")


# ------------------------------------------------------------------
# ping
# ------------------------------------------------------------------


class TestPing:
    def test_ping_success(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": [{"name": "test"}]})
        result = client.ping()
        assert result["status"] == "ok"
        assert "response_time_s" in result

    def test_ping_failure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "bad auth"}}
        )
        result = client.ping()
        assert result["status"] == "error"
        assert "response_time_s" in result


# ------------------------------------------------------------------
# URL construction
# ------------------------------------------------------------------


class TestURLConstruction:
    def test_table_url(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        client.get_records("alm_hardware")
        url = client._session.get.call_args[0][0]
        assert url == "https://test.service-now.com/api/now/table/alm_hardware"

    def test_record_url(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": {}})
        client.get_record("alm_hardware", "abc123")
        url = client._session.get.call_args[0][0]
        assert url == "https://test.service-now.com/api/now/table/alm_hardware/abc123"
