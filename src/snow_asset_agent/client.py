"""ServiceNow REST client for asset tables.

Handles all HTTP communication with the ServiceNow Table API, including
authentication, query building, pagination, retry logic, and error
mapping to the custom exception hierarchy.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from snow_asset_agent.config import AssetAgentConfig, get_config
from snow_asset_agent.exceptions import (
    ServiceNowAPIError,
    ServiceNowAuthError,
    ServiceNowConnectionError,
    ServiceNowNotFoundError,
    ServiceNowPermissionError,
    ServiceNowRateLimitError,
)

logger = logging.getLogger(__name__)


class ServiceNowClient:
    """Low-level REST client for the ServiceNow Table API.

    Parameters
    ----------
    config:
        If *None*, the global singleton from :func:`get_config` is used.
    """

    def __init__(self, config: AssetAgentConfig | None = None) -> None:
        self._config = config or get_config()
        self._base_url = self._config.base_url
        self._session = self._build_session()

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = self._config.auth
        session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        retry = Retry(
            total=self._config.servicenow_max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    # ------------------------------------------------------------------
    # Error mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(response: requests.Response, table: str) -> None:
        """Map HTTP status codes to typed exceptions."""
        if response.ok:
            return

        status = response.status_code
        try:
            body = response.json()
            detail = body.get("error", {}).get("message", response.text[:300])
        except Exception:
            detail = response.text[:300]

        if status == 401:
            raise ServiceNowAuthError(
                f"Authentication failed for table '{table}': {detail}",
                status_code=status,
                table_name=table,
            )
        if status == 403:
            raise ServiceNowPermissionError(
                f"Permission denied for table '{table}': {detail}",
                status_code=status,
                table_name=table,
            )
        if status == 404:
            raise ServiceNowNotFoundError(
                f"Not found on table '{table}': {detail}",
                status_code=status,
                table_name=table,
            )
        if status == 429:
            raise ServiceNowRateLimitError(
                f"Rate-limited on table '{table}': {detail}",
                status_code=status,
                table_name=table,
            )
        raise ServiceNowAPIError(
            f"API error {status} on table '{table}': {detail}",
            status_code=status,
            table_name=table,
        )

    # ------------------------------------------------------------------
    # Public CRUD methods
    # ------------------------------------------------------------------

    def get_records(
        self,
        table: str,
        *,
        query: str = "",
        fields: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
        display_value: str = "false",
    ) -> list[dict[str, Any]]:
        """Fetch multiple records from *table*.

        Returns a list of dicts (the ``result`` array from the ServiceNow
        response envelope).
        """
        url = f"{self._base_url}/table/{table}"
        params: dict[str, Any] = {
            "sysparm_limit": limit,
            "sysparm_offset": offset,
            "sysparm_display_value": display_value,
        }
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = ",".join(fields)

        logger.debug("GET %s params=%s", url, {k: v for k, v in params.items()})

        try:
            resp = self._session.get(url, params=params, timeout=self._config.servicenow_timeout)
        except requests.ConnectionError as exc:
            raise ServiceNowConnectionError(
                f"Connection error reaching '{table}': {exc}",
                table_name=table,
            ) from exc
        except requests.Timeout as exc:
            raise ServiceNowConnectionError(
                f"Timeout reaching '{table}': {exc}",
                table_name=table,
            ) from exc

        self._raise_for_status(resp, table)
        data = resp.json()
        return data.get("result", [])

    def get_record(
        self,
        table: str,
        sys_id: str,
        *,
        fields: list[str] | None = None,
        display_value: str = "false",
    ) -> dict[str, Any]:
        """Fetch a single record by *sys_id*."""
        url = f"{self._base_url}/table/{table}/{sys_id}"
        params: dict[str, Any] = {"sysparm_display_value": display_value}
        if fields:
            params["sysparm_fields"] = ",".join(fields)

        logger.debug("GET %s", url)

        try:
            resp = self._session.get(url, params=params, timeout=self._config.servicenow_timeout)
        except requests.ConnectionError as exc:
            raise ServiceNowConnectionError(
                f"Connection error reaching '{table}/{sys_id}': {exc}",
                table_name=table,
                sys_id=sys_id,
            ) from exc
        except requests.Timeout as exc:
            raise ServiceNowConnectionError(
                f"Timeout reaching '{table}/{sys_id}': {exc}",
                table_name=table,
                sys_id=sys_id,
            ) from exc

        self._raise_for_status(resp, table)
        data = resp.json()
        return data.get("result", {})

    def create_record(
        self,
        table: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new record in *table*."""
        url = f"{self._base_url}/table/{table}"
        logger.debug("POST %s", url)

        try:
            resp = self._session.post(url, json=data, timeout=self._config.servicenow_timeout)
        except requests.ConnectionError as exc:
            raise ServiceNowConnectionError(
                f"Connection error creating record in '{table}': {exc}",
                table_name=table,
            ) from exc
        except requests.Timeout as exc:
            raise ServiceNowConnectionError(
                f"Timeout creating record in '{table}': {exc}",
                table_name=table,
            ) from exc

        self._raise_for_status(resp, table)
        return resp.json().get("result", {})

    def update_record(
        self,
        table: str,
        sys_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing record identified by *sys_id*."""
        url = f"{self._base_url}/table/{table}/{sys_id}"
        logger.debug("PATCH %s", url)

        try:
            resp = self._session.patch(url, json=data, timeout=self._config.servicenow_timeout)
        except requests.ConnectionError as exc:
            raise ServiceNowConnectionError(
                f"Connection error updating '{table}/{sys_id}': {exc}",
                table_name=table,
                sys_id=sys_id,
            ) from exc
        except requests.Timeout as exc:
            raise ServiceNowConnectionError(
                f"Timeout updating '{table}/{sys_id}': {exc}",
                table_name=table,
                sys_id=sys_id,
            ) from exc

        self._raise_for_status(resp, table)
        return resp.json().get("result", {})

    def delete_record(
        self,
        table: str,
        sys_id: str,
    ) -> bool:
        """Delete a record.  Returns *True* on success."""
        url = f"{self._base_url}/table/{table}/{sys_id}"
        logger.debug("DELETE %s", url)

        try:
            resp = self._session.delete(url, timeout=self._config.servicenow_timeout)
        except requests.ConnectionError as exc:
            raise ServiceNowConnectionError(
                f"Connection error deleting '{table}/{sys_id}': {exc}",
                table_name=table,
                sys_id=sys_id,
            ) from exc
        except requests.Timeout as exc:
            raise ServiceNowConnectionError(
                f"Timeout deleting '{table}/{sys_id}': {exc}",
                table_name=table,
                sys_id=sys_id,
            ) from exc

        self._raise_for_status(resp, table)
        return True

    # ------------------------------------------------------------------
    # Convenience: health ping
    # ------------------------------------------------------------------

    def ping(self) -> dict[str, Any]:
        """Lightweight connectivity check (fetches 1 record from sys_properties)."""
        start = time.monotonic()
        try:
            self.get_records("sys_properties", limit=1)
            elapsed = round(time.monotonic() - start, 3)
            return {"status": "ok", "response_time_s": elapsed}
        except ServiceNowError as exc:
            elapsed = round(time.monotonic() - start, 3)
            return {"status": "error", "error": str(exc), "response_time_s": elapsed}


# Re-export for convenience
ServiceNowError = ServiceNowConnectionError.__bases__[0]
