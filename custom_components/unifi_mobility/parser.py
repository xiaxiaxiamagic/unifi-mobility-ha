"""Firmware-tolerant value parsing for UniFi Mobility."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def as_bool(value: Any) -> bool | None:
    """Convert common UMR boolean representations without truthiness surprises."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "enabled", "connected"}:
            return True
        if normalized in {"0", "false", "no", "off", "disabled", "disconnected", ""}:
            return False
    return None


def as_int(value: Any) -> int | None:
    """Convert a numeric UMR value to an integer."""
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return None


def first(data: Any, *keys: str) -> Any:
    """Return the first present value from a firmware-dependent mapping."""
    if not isinstance(data, dict):
        return None
    return next((data[key] for key in keys if data.get(key) is not None), None)


def nested(data: dict[str, Any], section: str, *keys: str) -> Any:
    """Safely read a nested value."""
    value: Any = data.get(section, {})
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def data_usage(data: dict[str, Any]) -> int | None:
    return as_int(first(data.get("medium"), "total_usage", "data_usage", "usage"))


def data_limit(data: dict[str, Any]) -> int | None:
    usage = nested(data, "networks", "data_usage")
    return as_int(first(usage, "limit", "data_limit", "quota"))


def data_remaining(data: dict[str, Any]) -> int | None:
    used, limit = data_usage(data), data_limit(data)
    if used is None or limit is None or limit <= 0:
        return None
    return max(limit - used, 0)


def data_usage_percent(data: dict[str, Any]) -> float | None:
    used, limit = data_usage(data), data_limit(data)
    if used is None or limit is None or limit <= 0:
        return None
    return round(min(used / limit * 100, 100), 1)


def days_until_billing(data: dict[str, Any], today: date | None = None) -> int | None:
    """Calculate days until a day-of-month or ISO billing date."""
    raw = nested(data, "networks", "data_usage", "billing_cycle_date")
    if raw is None:
        return None
    today = today or date.today()
    if isinstance(raw, str) and "-" in raw:
        try:
            target = datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return max((target - today).days, 0)
        except ValueError:
            return None
    day = as_int(raw)
    if day is None or not 1 <= day <= 31:
        return None
    for month_offset in (0, 1):
        month = today.month + month_offset
        year = today.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        try:
            target = date(year, month, day)
        except ValueError:
            continue
        if target >= today:
            return (target - today).days
    return None
