"""Custom exception hierarchy for snow-asset-agent.

All exceptions inherit from ServiceNowError, which serves as the base
for catching any snow-asset-agent related error.
"""

from __future__ import annotations


class ServiceNowError(Exception):
    """Base exception for all snow-asset-agent errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        table_name: str | None = None,
        sys_id: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.table_name = table_name
        self.sys_id = sys_id
        super().__init__(message)

    def __repr__(self) -> str:
        parts = [f"message={self.message!r}"]
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        if self.table_name is not None:
            parts.append(f"table_name={self.table_name!r}")
        if self.sys_id is not None:
            parts.append(f"sys_id={self.sys_id!r}")
        return f"{type(self).__name__}({', '.join(parts)})"


class ServiceNowConnectionError(ServiceNowError):
    """Cannot reach the ServiceNow instance (network / DNS / timeout)."""


class ServiceNowAuthError(ServiceNowError):
    """Authentication or authorisation failure (HTTP 401/403)."""


class ServiceNowNotFoundError(ServiceNowError):
    """Requested record was not found (HTTP 404)."""


class ServiceNowPermissionError(ServiceNowError):
    """Insufficient permissions to access the resource (HTTP 403)."""


class ServiceNowRateLimitError(ServiceNowError):
    """Rate-limited by the ServiceNow instance (HTTP 429)."""


class ServiceNowAPIError(ServiceNowError):
    """General API error not covered by a more specific subclass."""
