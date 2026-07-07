"""Focused entity and coordinator behavior tests."""

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.unifi_mobility.button import BUTTONS, MobilityButton
from custom_components.unifi_mobility.coordinator import UnifiMobilityCoordinator
from custom_components.unifi_mobility.select import SELECTS, MobilitySelect
from custom_components.unifi_mobility.sensor import signal_quality
from custom_components.unifi_mobility.switch import SWITCHES, MobilitySwitch


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
    coordinator._section_updated = {"low": 290.0, "device": 10.0}
    coordinator.entry = SimpleNamespace(options={})
    coordinator._update_interval = timedelta(seconds=10)
    monkeypatch.setattr(
        "custom_components.unifi_mobility.coordinator.monotonic", lambda: 300.0
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


@pytest.mark.asyncio
async def test_restart_button() -> None:
    button = object.__new__(MobilityButton)
    button.entity_description = BUTTONS[2]
    button.coordinator = SimpleNamespace(async_restart_device=AsyncMock())
    await button.async_press()
    button.coordinator.async_restart_device.assert_awaited_once()


def test_control_entity_states() -> None:
    coordinator = SimpleNamespace(
        data={
            "locate": {"locate_on": True},
            "powers": {"poe": False},
            "radio_preference": {
                "mode": ["gsm", "umts", "lte"],
                "lte_band": ["3"],
            },
            "radio_capability": {"lte_band": ["1", "3", "20"]},
            "sim_profile": {
                "current": {"apn": "custom"},
                "default": {"apn": "carrier"},
            },
        }
    )
    locate = object.__new__(MobilitySwitch)
    locate.entity_description = SWITCHES[0]
    locate.coordinator = coordinator
    poe = object.__new__(MobilitySwitch)
    poe.entity_description = SWITCHES[1]
    poe.coordinator = coordinator
    assert locate.is_on is True
    assert poe.is_on is False

    network_mode = object.__new__(MobilitySelect)
    network_mode.entity_description = SELECTS[0]
    network_mode.coordinator = coordinator
    lte_band = object.__new__(MobilitySelect)
    lte_band.entity_description = SELECTS[1]
    lte_band.coordinator = coordinator
    sim_source = object.__new__(MobilitySelect)
    sim_source.entity_description = SELECTS[2]
    sim_source.coordinator = coordinator
    assert network_mode.current_option == "automatic"
    assert lte_band.options == ["AUTO", "B1", "B3", "B20"]
    assert lte_band.current_option == "B3"
    assert sim_source.current_option == "custom"


@pytest.mark.asyncio
async def test_control_rpc_payloads() -> None:
    coordinator = object.__new__(UnifiMobilityCoordinator)
    coordinator._control_lock = asyncio.Lock()
    coordinator._cycle = 5
    coordinator._cache = {
        "radio_preference": {
            "mode": ["lte", "umts"],
            "lte_band": ["AUTO"],
            "band": ["AUTO"],
        },
        "radio_capability": {"lte_band": ["1", "3", "20"]},
        "sim_profile": {
            "current": {"apn": "custom", "password": "secret"},
            "default": {"apn": "carrier", "password": "default-secret"},
        },
    }
    coordinator.api = SimpleNamespace(async_call=AsyncMock(return_value={"ok": True}))
    coordinator.async_request_refresh = AsyncMock()

    await coordinator.async_set_network_mode("lte_only")
    coordinator.api.async_call.assert_awaited_with(
        "SetRadioPreference",
        {"mode": ["lte"], "lte_band": ["AUTO"], "band": ["AUTO"]},
    )
    await coordinator.async_set_lte_band("B3")
    coordinator.api.async_call.assert_awaited_with(
        "SetRadioPreference",
        {"mode": ["lte", "umts"], "lte_band": ["3"], "band": ["AUTO"]},
    )
    await coordinator.async_set_sim_profile_source("automatic")
    coordinator.api.async_call.assert_awaited_with(
        "SetSimProfile",
        {
            "apn": "carrier",
            "password": "default-secret",
            "apn_configuration_source": 1,
        },
    )
    assert coordinator.async_request_refresh.await_count == 3
