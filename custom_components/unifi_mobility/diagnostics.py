"""Diagnostics support for UniFi Mobility."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT = {
    "password",
    "host",
    "token",
    "ubus_rpc_session",
    "mac",
    "imei",
    "iccid",
    "geo_ip",
    "wan_ip",
    "wan_ipv6",
    "lan_ip",
    "lan_ipv6",
    "cloud_url",
    "initial_setup_ssid",
}


def _redact_nested(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if key.lower() == "clients":
                redacted[key] = {"count": len(item) if isinstance(item, dict) else 0}
            elif key.lower() in TO_REDACT:
                redacted[key] = "**REDACTED**"
            else:
                redacted[key] = _redact_nested(item)
        return redacted
    if isinstance(value, list):
        return [_redact_nested(item) for item in value]
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return credentials- and identifier-free diagnostics."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(
            {"data": dict(entry.data), "options": dict(entry.options)}, TO_REDACT
        ),
        "last_update_success": coordinator.last_update_success,
        "data": _redact_nested(coordinator.data),
    }
