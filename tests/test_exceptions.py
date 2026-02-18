"""Tests for snow_asset_agent.exceptions."""

from __future__ import annotations

import pytest

from snow_asset_agent.exceptions import (
    ServiceNowAPIError,
    ServiceNowAuthError,
    ServiceNowConnectionError,
    ServiceNowError,
    ServiceNowNotFoundError,
    ServiceNowPermissionError,
    ServiceNowRateLimitError,
)


class TestExceptionHierarchy:
    """Verify that every exception inherits from ServiceNowError."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            ServiceNowConnectionError,
            ServiceNowAuthError,
            ServiceNowNotFoundError,
            ServiceNowPermissionError,
            ServiceNowRateLimitError,
            ServiceNowAPIError,
        ],
    )
    def test_inherits_from_base(self, exc_cls):
        assert issubclass(exc_cls, ServiceNowError)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            ServiceNowConnectionError,
            ServiceNowAuthError,
            ServiceNowNotFoundError,
            ServiceNowPermissionError,
            ServiceNowRateLimitError,
            ServiceNowAPIError,
        ],
    )
    def test_inherits_from_exception(self, exc_cls):
        assert issubclass(exc_cls, Exception)


class TestServiceNowError:
    """Test the base exception attributes and repr."""

    def test_message(self):
        exc = ServiceNowError("boom")
        assert str(exc) == "boom"
        assert exc.message == "boom"

    def test_status_code(self):
        exc = ServiceNowError("fail", status_code=500)
        assert exc.status_code == 500

    def test_table_name(self):
        exc = ServiceNowError("fail", table_name="alm_hardware")
        assert exc.table_name == "alm_hardware"

    def test_sys_id(self):
        exc = ServiceNowError("fail", sys_id="abc123")
        assert exc.sys_id == "abc123"

    def test_defaults_are_none(self):
        exc = ServiceNowError("msg")
        assert exc.status_code is None
        assert exc.table_name is None
        assert exc.sys_id is None

    def test_repr_minimal(self):
        exc = ServiceNowError("msg")
        assert "ServiceNowError" in repr(exc)
        assert "msg" in repr(exc)

    def test_repr_full(self):
        exc = ServiceNowError("fail", status_code=404, table_name="t", sys_id="x")
        r = repr(exc)
        assert "status_code=404" in r
        assert "table_name='t'" in r
        assert "sys_id='x'" in r

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ServiceNowError):
            raise ServiceNowError("test")

    def test_catch_subclass_via_base(self):
        with pytest.raises(ServiceNowError):
            raise ServiceNowAuthError("auth failed", status_code=401)


class TestSpecificExceptions:
    """Test that each subclass works correctly."""

    def test_connection_error(self):
        exc = ServiceNowConnectionError("timeout", table_name="alm_hardware")
        assert exc.table_name == "alm_hardware"
        assert "timeout" in str(exc)

    def test_auth_error(self):
        exc = ServiceNowAuthError("bad creds", status_code=401)
        assert exc.status_code == 401

    def test_not_found_error(self):
        exc = ServiceNowNotFoundError("gone", status_code=404, sys_id="xyz")
        assert exc.status_code == 404
        assert exc.sys_id == "xyz"

    def test_permission_error(self):
        exc = ServiceNowPermissionError("forbidden", status_code=403)
        assert exc.status_code == 403

    def test_rate_limit_error(self):
        exc = ServiceNowRateLimitError("slow down", status_code=429)
        assert exc.status_code == 429

    def test_api_error(self):
        exc = ServiceNowAPIError("server error", status_code=500, table_name="alm_asset")
        assert exc.status_code == 500
        assert exc.table_name == "alm_asset"
