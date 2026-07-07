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

SAFE_DATA_FIELDS: dict[str, Any] = {
    "low": {"fw": None, "geo_isp": None, "network_source": None, "uptime": None},
    "medium": {"cpu": None, "memory": None, "total_usage": None},
    "high": {
        "rssi": None,
        "rsrp": None,
        "rsrq": None,
        "rx_channel": None,
        "tx_channel": None,
    },
    "status": {
        "online": None,
        "activated": None,
        "lte": {
            "band": None,
            "network_type": None,
            "rat": None,
            "access_technology": None,
            "registration_type": None,
            "sim_present": None,
            "pin_lock": None,
        },
    },
    "device": {"model_name": None, "lte_model_name": None, "uptime": None},
    "networks": {
        "data_usage": {
            "limit": None,
            "data_limit": None,
            "quota": None,
            "billing_cycle_date": None,
        }
    },
    "powers": {"poe": None},
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


def _allowlist_data(value: Any, fields: Any) -> Any:
    """Copy only explicitly safe diagnostic fields from firmware data."""
    if fields is None:
        return value
    if not isinstance(value, dict) or not isinstance(fields, dict):
        return None
    return {
        key: _allowlist_data(value[key], child_fields)
        for key, child_fields in fields.items()
        if key in value
    }


def _safe_diagnostics_data(data: dict[str, Any]) -> dict[str, Any]:
    """Return useful telemetry without unknown firmware fields or identifiers."""
    safe = _allowlist_data(data, SAFE_DATA_FIELDS)
    clients = data.get("clients")
    if isinstance(clients, (dict, list)):
        safe["clients"] = {"count": len(clients)}
    return safe


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
        "last_update_success_time": coordinator.last_success_time,
        "polling_health": coordinator.diagnostic_data(),
        "data": _safe_diagnostics_data(coordinator.data),
    }
