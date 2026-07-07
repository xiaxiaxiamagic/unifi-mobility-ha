"""Safe switch controls for UniFi Mobility."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UnifiMobilityCoordinator
from .entity import UnifiMobilityEntity


@dataclass(frozen=True, kw_only=True)
class MobilitySwitchDescription(SwitchEntityDescription):
    control: str
    section: str


SWITCHES = (
    MobilitySwitchDescription(
        key="locate",
        translation_key="locate",
        icon="mdi:crosshairs-gps",
        control="locate",
        section="locate",
    ),
    MobilitySwitchDescription(
        key="poe_passthrough_control",
        translation_key="poe_passthrough_control",
        icon="mdi:power-plug",
        control="poe",
        section="powers",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: UnifiMobilityCoordinator = entry.runtime_data
    async_add_entities(
        MobilitySwitch(coordinator, entry, description)
        for description in SWITCHES
        if coordinator.section_available(description.section)
    )


class MobilitySwitch(UnifiMobilityEntity, SwitchEntity):
    """A writable UMR switch backed by the local portal API."""

    entity_description: MobilitySwitchDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._identity}_{description.key}"
        self._attr_suggested_object_id = (
            f"{self._attr_suggested_object_id}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.control == "locate":
            return self.coordinator.data.get("locate", {}).get("locate_on")
        return self.coordinator.data.get("powers", {}).get("poe")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.section_available(
            self.entity_description.section
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set_state(False)

    async def _async_set_state(self, enabled: bool) -> None:
        if self.entity_description.control == "locate":
            await self.coordinator.async_set_locate(enabled)
        else:
            await self.coordinator.async_set_poe_passthrough(enabled)
