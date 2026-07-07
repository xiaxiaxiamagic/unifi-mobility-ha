"""Tests for diagnostics privacy and polling health."""

from datetime import timedelta

from custom_components.unifi_mobility.coordinator import UnifiMobilityCoordinator
from custom_components.unifi_mobility.diagnostics import _redact_nested


def test_sensitive_values_are_redacted() -> None:
    data = {
        "host": "192.0.2.1",
        "device": {"imei": "123", "model": "UMR"},
        "clients": {"aa:bb": {"name": "phone"}},
    }
    redacted = _redact_nested(data)
    assert redacted["host"] == "**REDACTED**"
    assert redacted["device"]["imei"] == "**REDACTED**"
    assert redacted["device"]["model"] == "UMR"
    assert redacted["clients"] == {"count": 1}


def test_nested_lists_are_redacted() -> None:
    assert _redact_nested([{"iccid": "secret"}]) == [{"iccid": "**REDACTED**"}]


def test_polling_health_diagnostics(monkeypatch) -> None:
    coordinator = object.__new__(UnifiMobilityCoordinator)
    coordinator._cycle = 8
    coordinator._base_interval = 30
    coordinator._failure_count = 2
    coordinator._method_failures = {"InfoHighDump": 3}
    coordinator._section_updated = {"low": 90.0}
    coordinator.update_interval = timedelta(seconds=120)
    monkeypatch.setattr(
        "custom_components.unifi_mobility.coordinator.monotonic", lambda: 100.0
    )

    assert coordinator.diagnostic_data() == {
        "poll_cycle": 8,
        "base_interval_seconds": 30,
        "current_interval_seconds": 120.0,
        "consecutive_failures": 2,
        "rpc_failure_counts": {"InfoHighDump": 3},
        "section_age_seconds": {"low": 10.0},
    }
