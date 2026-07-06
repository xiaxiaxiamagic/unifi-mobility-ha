"""Safe diagnostic buttons for UniFi Mobility."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UnifiMobilityCoordinator
from .entity import UnifiMobilityEntity


@dataclass(frozen=True, kw_only=True)
class MobilityButtonDescription(ButtonEntityDescription):
    action: str


BUTTONS = (
    MobilityButtonDescription(
        key="refresh",
        translation_key="refresh",
        icon="mdi:refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        action="refresh",
    ),
    MobilityButtonDescription(
        key="reconnect",
        translation_key="reconnect",
        icon="mdi:connection",
        entity_category=EntityCategory.DIAGNOSTIC,
        action="reconnect",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: UnifiMobilityCoordinator = entry.runtime_data
    async_add_entities(
        MobilityButton(coordinator, entry, description) for description in BUTTONS
    )


class MobilityButton(UnifiMobilityEntity, ButtonEntity):
    """A read-only UMR diagnostic action."""

    entity_description: MobilityButtonDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._identity}_{description.key}"
        self._attr_suggested_object_id = (
            f"{self._attr_suggested_object_id}_{description.key}"
        )

    async def async_press(self) -> None:
        if self.entity_description.action == "reconnect":
            await self.coordinator.async_reconnect()
        else:
            await self.coordinator.async_request_refresh()
