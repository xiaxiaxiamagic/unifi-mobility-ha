"""Tests for firmware-tolerant value parsing."""

from datetime import date
from zoneinfo import ZoneInfo

import pytest

from custom_components.unifi_mobility.parser import (
    as_bool,
    billing_date,
    data_remaining,
    data_usage_percent,
    days_until_billing,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        ("true", True),
        ("false", False),
        ("connected", True),
        ("disabled", False),
        (None, None),
        ("unknown", None),
    ],
)
def test_as_bool(raw, expected) -> None:
    assert as_bool(raw) is expected


def test_data_plan_calculations() -> None:
    data = {
        "medium": {"total_usage": "250"},
        "networks": {"data_usage": {"limit": 1000}},
    }
    assert data_remaining(data) == 750
    assert data_usage_percent(data) == 25.0


def test_data_plan_without_limit() -> None:
    assert data_remaining({"medium": {"total_usage": 12}}) is None
    assert data_usage_percent({"medium": {"total_usage": 12}}) is None


def test_days_until_billing_day() -> None:
    data = {"networks": {"data_usage": {"billing_cycle_date": 15}}}
    assert days_until_billing(data, date(2026, 7, 10)) == 5
    assert days_until_billing(data, date(2026, 7, 20)) == 26


def test_days_until_iso_billing_date() -> None:
    data = {"networks": {"data_usage": {"billing_cycle_date": "2026-07-20"}}}
    assert days_until_billing(data, date(2026, 7, 10)) == 10


def test_unix_billing_timestamp_uses_local_date() -> None:
    data = {"networks": {"data_usage": {"billing_cycle_date": 1785513600}}}
    timezone = ZoneInfo("Asia/Shanghai")
    assert billing_date(data, date(2026, 7, 6), timezone) == date(2026, 8, 1)
    assert days_until_billing(data, date(2026, 7, 6), timezone) == 26
