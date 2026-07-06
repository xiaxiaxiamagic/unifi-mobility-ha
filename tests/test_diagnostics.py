"""Tests for diagnostics privacy."""

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
