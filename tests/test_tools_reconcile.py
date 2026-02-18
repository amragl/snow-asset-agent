"""Tests for snow_asset_agent.tools.reconcile."""

from __future__ import annotations

import requests

from snow_asset_agent.tools.reconcile import reconcile_assets_to_cis
from tests.helpers import make_ci_record, make_hardware_record, make_mock_response


class TestReconcileAssetsToCis:
    def test_fully_matched(self, client_with_mock_session):
        client = client_with_mock_session
        asset = make_hardware_record(sys_id="a1", ci="ci1")
        ci = make_ci_record(sys_id="ci1", name="server-1")
        # First call: assets, second: CIs
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [asset]}),
            make_mock_response(json_data={"result": [ci]}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["matched_count"] == 1
        assert result["unmatched_assets_count"] == 0

    def test_unmatched_asset(self, client_with_mock_session):
        client = client_with_mock_session
        asset = make_hardware_record(sys_id="a1", ci="")
        ci = make_ci_record(sys_id="ci1")
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [asset]}),
            make_mock_response(json_data={"result": [ci]}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["unmatched_assets_count"] == 1
        assert result["matched_count"] == 0

    def test_unmatched_ci(self, client_with_mock_session):
        client = client_with_mock_session
        asset = make_hardware_record(sys_id="a1", ci="ci1")
        ci1 = make_ci_record(sys_id="ci1")
        ci2 = make_ci_record(sys_id="ci2", name="orphan-ci")
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [asset]}),
            make_mock_response(json_data={"result": [ci1, ci2]}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["unmatched_cis_count"] == 1

    def test_empty_assets(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": [make_ci_record()]}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["matched_count"] == 0
        assert result["unmatched_cis_count"] == 1

    def test_empty_cis(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [make_hardware_record(ci="ci1")]}),
            make_mock_response(json_data={"result": []}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["matched_count"] == 0
        assert result["unmatched_assets_count"] == 1

    def test_both_empty(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["matched_count"] == 0
        assert result["unmatched_assets_count"] == 0
        assert result["unmatched_cis_count"] == 0

    def test_ci_as_dict(self, client_with_mock_session):
        client = client_with_mock_session
        asset = make_hardware_record(sys_id="a1")
        asset["ci"] = {"value": "ci1", "display_value": "Server A"}
        ci = make_ci_record(sys_id="ci1")
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [asset]}),
            make_mock_response(json_data={"result": [ci]}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["matched_count"] == 1

    def test_model_category_filter(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        reconcile_assets_to_cis(client=client, model_category="Computer")
        first_call_params = client._session.get.call_args_list[0][1].get("params", {})
        assert "Computer" in str(first_call_params)

    def test_invalid_limit(self, client_with_mock_session):
        result = reconcile_assets_to_cis(client=client_with_mock_session, limit=0)
        assert "error" in result

    def test_connection_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.ConnectionError("fail")
        result = reconcile_assets_to_cis(client=client)
        assert "error" in result

    def test_401_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.return_value = make_mock_response(
            status_code=401, ok=False, json_data={"error": {"message": "unauth"}}
        )
        result = reconcile_assets_to_cis(client=client)
        assert "error" in result

    def test_output_structure(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": []}),
            make_mock_response(json_data={"result": []}),
        ]
        result = reconcile_assets_to_cis(client=client)
        for key in [
            "matched",
            "matched_count",
            "unmatched_assets",
            "unmatched_assets_count",
            "unmatched_cis",
            "unmatched_cis_count",
        ]:
            assert key in result

    def test_matched_item_structure(self, client_with_mock_session):
        client = client_with_mock_session
        asset = make_hardware_record(sys_id="a1", ci="ci1")
        ci = make_ci_record(sys_id="ci1")
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [asset]}),
            make_mock_response(json_data={"result": [ci]}),
        ]
        result = reconcile_assets_to_cis(client=client)
        m = result["matched"][0]
        assert "asset_sys_id" in m
        assert "ci_sys_id" in m

    def test_multiple_assets_and_cis(self, client_with_mock_session):
        client = client_with_mock_session
        assets = [
            make_hardware_record(sys_id="a1", ci="ci1"),
            make_hardware_record(sys_id="a2", ci="ci2"),
            make_hardware_record(sys_id="a3", ci=""),
        ]
        cis = [
            make_ci_record(sys_id="ci1"),
            make_ci_record(sys_id="ci2"),
            make_ci_record(sys_id="ci3"),
        ]
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": assets}),
            make_mock_response(json_data={"result": cis}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["matched_count"] == 2
        assert result["unmatched_assets_count"] == 1
        assert result["unmatched_cis_count"] == 1

    def test_timeout_error(self, client_with_mock_session):
        client = client_with_mock_session
        client._session.get.side_effect = requests.Timeout("timed out")
        result = reconcile_assets_to_cis(client=client)
        assert "error" in result

    def test_negative_limit(self, client_with_mock_session):
        result = reconcile_assets_to_cis(client=client_with_mock_session, limit=-1)
        assert "error" in result

    def test_none_ci_field(self, client_with_mock_session):
        client = client_with_mock_session
        asset = make_hardware_record(sys_id="a1", ci=None)
        client._session.get.side_effect = [
            make_mock_response(json_data={"result": [asset]}),
            make_mock_response(json_data={"result": []}),
        ]
        result = reconcile_assets_to_cis(client=client)
        assert result["unmatched_assets_count"] == 1
