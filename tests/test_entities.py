"""Focused entity and coordinator behavior tests."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.unifi_mobility.button import BUTTONS, MobilityButton
from custom_components.unifi_mobility.coordinator import UnifiMobilityCoordinator
from custom_components.unifi_mobility.sensor import signal_quality


@pytest.mark.parametrize(
    ("rsrp", "expected"),
    [
        (-70, "excellent"),
        (-85, "good"),
        (-95, "fair"),
        (-110, "poor"),
        (None, "no_signal"),
    ],
)
def test_signal_quality(rsrp, expected) -> None:
    assert signal_quality(rsrp) == expected


def test_section_availability(monkeypatch) -> None:
    coordinator = object.__new__(UnifiMobilityCoordinator)
    coordinator._cache = {"low": {}, "device": {}}
    coordinator._section_updated = {"low": 90.0, "device": 10.0}
    coordinator.entry = SimpleNamespace(options={})
    coordinator._update_interval = timedelta(seconds=10)
    monkeypatch.setattr(
        "custom_components.unifi_mobility.coordinator.monotonic", lambda: 100.0
    )
    assert coordinator.section_available("low")
    assert not coordinator.section_available("device")
    assert not coordinator.section_available("missing")


@pytest.mark.asyncio
async def test_refresh_button() -> None:
    button = object.__new__(MobilityButton)
    button.entity_description = BUTTONS[0]
    button.coordinator = SimpleNamespace(async_request_refresh=AsyncMock())
    await button.async_press()
    button.coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconnect_button() -> None:
    button = object.__new__(MobilityButton)
    button.entity_description = BUTTONS[1]
    button.coordinator = SimpleNamespace(async_reconnect=AsyncMock())
    await button.async_press()
    button.coordinator.async_reconnect.assert_awaited_once()
