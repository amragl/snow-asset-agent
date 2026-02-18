"""Tests for snow_asset_agent.tools.depreciation."""

from __future__ import annotations

from datetime import date, timedelta

import requests

from snow_asset_agent.tools.depreciation import (
    DEFAULT_USEFUL_LIFE,
    FALLBACK_USEFUL_LIFE,
    _parse_date,
    _safe_float,
    track_asset_depreciation,
)
from tests.helpers import make_hardware_record, make_mock_response


class TestSafeFloat:
    def test_valid(self):
        assert _safe_float("100") == 100.0

    def test_none(self):
        assert _safe_float(None) == 0.0

    def test_empty(self):
        assert _safe_float("") == 0.0

    def test_invalid(self):
        assert _safe_float("abc") == 0.0


class TestParseDate:
    def test_valid(self):
        assert _parse_date("2024-01-15") == date(2024, 1, 15)

    def test_none(self):
        assert _parse_date(None) is None

    def test_empty(self):
        assert _parse_date("") is None

    def test_invalid(self):
        assert _parse_date("bad") is None


class TestDefaultUsefulLife:
    def test_computer(self):
        assert DEFAULT_USEFUL_LIFE["Computer"] == 3

    def test_server(self):
        assert DEFAULT_USEFUL_LIFE["Server"] == 5

    def test_network_gear(self):
        assert DEFAULT_USEFUL_LIFE["Network Gear"] == 5

    def test_fallback(self):
        assert FALLBACK_USEFUL_LIFE == 4


class TestTrackAssetDepreciation:
    def test_happy_path(self, client_with_mock_session):
        client = client_with_mock_session
        three_years_ago = (date.today() - timedelta(days=365 * 3)).isoformat()
        rec = make_hardware_record(cost="3000", purchase_date=three_years_ago, model_category="Computer")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["count"] == 1
        asset = result["assets"][0]
        assert asset["cost"] == 3000.0
        assert asset["useful_life_years"] == 3

    def test_empty_results(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        result = track_asset_depreciation(client=client)
        assert result["count"] == 0

    def test_no_purchase_date_skipped(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="1000")
        rec.pop("purchase_date")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["count"] == 0

    def test_zero_cost_skipped(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="0", purchase_date="2023-01-01")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["count"] == 0

    def test_custom_useful_life(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="5000", purchase_date="2023-01-01", model_category="Computer")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client, useful_life_years=10)
        assert result["assets"][0]["useful_life_years"] == 10

    def test_model_category_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(json_data={"result": []})
        track_asset_depreciation(client=client, model_category="Server")
        params = client._session.get.call_args[1].get("params", {})
        assert "Server" in str(params)

    def test_current_value_not_negative(self, client_with_mock_session):
        client = client_with_mock_session
        ten_years_ago = (date.today() - timedelta(days=365 * 10)).isoformat()
        rec = make_hardware_record(cost="1000", purchase_date=ten_years_ago, model_category="Computer")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["assets"][0]["current_value"] >= 0

    def test_accumulated_not_exceed_cost(self, client_with_mock_session):
        client = client_with_mock_session
        ten_years_ago = (date.today() - timedelta(days=365 * 10)).isoformat()
        rec = make_hardware_record(cost="1000", purchase_date=ten_years_ago, model_category="Computer")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["assets"][0]["accumulated_depreciation"] <= 1000.0

    def test_invalid_limit(self, client_with_mock_session):
        result = track_asset_depreciation(client=client_with_mock_session, limit=0)
        assert "error" in result

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = track_asset_depreciation(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="2000", purchase_date="2023-01-01")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert "assets" in result
        assert "count" in result
        assert "total_accumulated_depreciation" in result

    def test_asset_item_structure(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="2000", purchase_date="2023-01-01")
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        asset = result["assets"][0]
        for key in [
            "sys_id",
            "asset_tag",
            "cost",
            "purchase_date",
            "useful_life_years",
            "years_owned",
            "annual_depreciation",
            "accumulated_depreciation",
            "current_value",
            "remaining_useful_life_years",
        ]:
            assert key in asset, f"Missing key: {key}"

    def test_model_category_as_dict(self, client_with_mock_session):
        client = client_with_mock_session
        rec = make_hardware_record(cost="3000", purchase_date="2023-01-01")
        rec["model_category"] = {"display_value": "Server", "value": "mc1"}
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["assets"][0]["useful_life_years"] == 5

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = track_asset_depreciation(client=client)
        assert "error" in result

    def test_negative_limit(self, client_with_mock_session):
        result = track_asset_depreciation(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_remaining_life_not_negative(self, client_with_mock_session):
        client = client_with_mock_session
        old_date = (date.today() - timedelta(days=365 * 20)).isoformat()
        rec = make_hardware_record(cost="1000", purchase_date=old_date)
        client._session.get.return_value = make_mock_response(json_data={"result": [rec]})
        result = track_asset_depreciation(client=client)
        assert result["assets"][0]["remaining_useful_life_years"] >= 0
