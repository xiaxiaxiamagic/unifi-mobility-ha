"""Binary sensors for UniFi Mobility."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UnifiMobilityCoordinator
from .entity import UnifiMobilityEntity
from .parser import as_bool


@dataclass(frozen=True, kw_only=True)
class MobilityBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]
    section: str


def lte_value(data: dict[str, Any], key: str) -> bool | None:
    lte = data.get("status", {}).get("lte", {})
    value = lte.get(key) if isinstance(lte, dict) else None
    return as_bool(value)


BINARY_SENSORS = (
    MobilityBinaryDescription(
        key="connectivity",
        translation_key="connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        section="status",
        value_fn=lambda d: (
            as_bool(d["status"]["online"])
            if d.get("status", {}).get("online") is not None
            else None
        ),
    ),
    MobilityBinaryDescription(
        key="sim_present",
        translation_key="sim_present",
        device_class=BinarySensorDeviceClass.PLUG,
        section="status",
        value_fn=lambda d: lte_value(d, "sim_present"),
    ),
    MobilityBinaryDescription(
        key="pin_locked",
        translation_key="pin_locked",
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=EntityCategory.DIAGNOSTIC,
        section="status",
        value_fn=lambda d: lte_value(d, "pin_lock"),
    ),
    MobilityBinaryDescription(
        key="activated",
        translation_key="activated",
        icon="mdi:check-decagram",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="status",
        value_fn=lambda d: (
            as_bool(d["status"]["activated"])
            if d.get("status", {}).get("activated") is not None
            else None
        ),
    ),
    MobilityBinaryDescription(
        key="poe_passthrough",
        translation_key="poe_passthrough",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        section="powers",
        value_fn=lambda d: (
            as_bool(d["powers"]["poe"])
            if d.get("powers", {}).get("poe") is not None
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: UnifiMobilityCoordinator = entry.runtime_data
    async_add_entities(
        MobilityBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class MobilityBinarySensor(UnifiMobilityEntity, BinarySensorEntity):
    """A UMR binary sensor."""

    entity_description: MobilityBinaryDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._identity}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.section_available(
            self.entity_description.section
        )
