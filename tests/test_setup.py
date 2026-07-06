"""Tests for capability-based setup and entity ID migration."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.unifi_mobility import async_migrate_entry
from custom_components.unifi_mobility.binary_sensor import (
    async_setup_entry as setup_binary,
)
from custom_components.unifi_mobility.sensor import async_setup_entry as setup_sensors


class FakeCoordinator:
    def __init__(self, data, sections) -> None:
        self.data = data
        self.sections = sections

    def section_available(self, section: str) -> bool:
        return section in self.sections

    def async_add_listener(self, *_args, **_kwargs):
        return lambda: None


@pytest.mark.asyncio
async def test_sensor_setup_uses_detected_capabilities() -> None:
    coordinator = FakeCoordinator({"low": {"fw": "1.2.3"}}, {"low"})
    entry = SimpleNamespace(
        runtime_data=coordinator,
        unique_id="device",
        title="UMR",
        data={"host": "192.0.2.1"},
    )
    added = []
    await setup_sensors(None, entry, lambda entities: added.extend(entities))
    assert [entity.entity_description.key for entity in added] == ["firmware"]


@pytest.mark.asyncio
async def test_false_binary_value_is_still_created() -> None:
    coordinator = FakeCoordinator({"status": {"online": False}}, {"status"})
    entry = SimpleNamespace(
        runtime_data=coordinator,
        unique_id="device",
        title="UMR",
        data={"host": "192.0.2.1"},
    )
    added = []
    await setup_binary(None, entry, lambda entities: added.extend(entities))
    assert [entity.entity_description.key for entity in added] == ["connectivity"]


@pytest.mark.asyncio
async def test_migration_renames_only_generated_ids() -> None:
    registry = MagicMock()

    def get_entity_id(_platform, _domain, unique_id):
        if unique_id.endswith("_firmware"):
            return "sensor.umr_industrial_eu"
        if unique_id.endswith("_operator"):
            return "sensor.my_custom_operator"
        return None

    registry.async_get_entity_id.side_effect = get_entity_id
    registry.async_get.return_value = None
    hass = SimpleNamespace(config_entries=MagicMock())
    entry = SimpleNamespace(version=1, unique_id="device", title="UMR Industrial EU")
    with patch("custom_components.unifi_mobility.er.async_get", return_value=registry):
        assert await async_migrate_entry(hass, entry)
    registry.async_update_entity.assert_called_once_with(
        "sensor.umr_industrial_eu",
        new_entity_id="sensor.umr_industrial_eu_firmware",
    )
    hass.config_entries.async_update_entry.assert_called_once_with(entry, version=2)
