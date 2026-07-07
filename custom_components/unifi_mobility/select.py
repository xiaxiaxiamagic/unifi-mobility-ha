"""Cellular configuration selects for UniFi Mobility."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UnifiMobilityCoordinator
from .entity import UnifiMobilityEntity


@dataclass(frozen=True, kw_only=True)
class MobilitySelectDescription(SelectEntityDescription):
    control: str
    section: str


SELECTS = (
    MobilitySelectDescription(
        key="network_mode",
        translation_key="network_mode",
        icon="mdi:network-strength-4-cog",
        options=("automatic", "lte_only", "umts_only"),
        control="network_mode",
        section="radio_preference",
    ),
    MobilitySelectDescription(
        key="lte_band_preference",
        translation_key="lte_band_preference",
        icon="mdi:signal",
        control="lte_band",
        section="radio_preference",
    ),
    MobilitySelectDescription(
        key="sim_profile_source",
        translation_key="sim_profile_source",
        icon="mdi:sim",
        options=("automatic", "custom"),
        control="sim_profile",
        section="sim_profile",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: UnifiMobilityCoordinator = entry.runtime_data
    async_add_entities(
        MobilitySelect(coordinator, entry, description)
        for description in SELECTS
        if coordinator.section_available(description.section)
        and (
            description.control != "lte_band"
            or coordinator.section_available("radio_capability")
        )
    )


class MobilitySelect(UnifiMobilityEntity, SelectEntity):
    """A writable UMR cellular setting."""

    entity_description: MobilitySelectDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._identity}_{description.key}"
        self._attr_suggested_object_id = (
            f"{self._attr_suggested_object_id}_{description.key}"
        )

    @property
    def options(self) -> list[str]:
        if self.entity_description.control != "lte_band":
            return list(self.entity_description.options)
        bands = self.coordinator.data.get("radio_capability", {}).get("lte_band", [])
        return ["AUTO", *(f"B{band}" for band in bands)]

    @property
    def current_option(self) -> str | None:
        control = self.entity_description.control
        if control == "network_mode":
            modes = set(
                self.coordinator.data.get("radio_preference", {}).get("mode", [])
            )
            if "lte" in modes and "umts" in modes:
                return "automatic"
            if modes == {"lte"}:
                return "lte_only"
            if modes == {"umts"}:
                return "umts_only"
            return None
        if control == "lte_band":
            values = self.coordinator.data.get("radio_preference", {}).get(
                "lte_band", []
            )
            value = str(values[0]) if values else "AUTO"
            return "AUTO" if value.upper() == "AUTO" else f"B{int(value)}"
        profile = self.coordinator.data.get("sim_profile", {})
        current, default = profile.get("current"), profile.get("default")
        if not isinstance(current, dict) or not isinstance(default, dict):
            return None
        return "automatic" if current == default else "custom"

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.section_available(
            self.entity_description.section
        )

    async def async_select_option(self, option: str) -> None:
        control = self.entity_description.control
        if control == "network_mode":
            await self.coordinator.async_set_network_mode(option)
        elif control == "lte_band":
            await self.coordinator.async_set_lte_band(option)
        else:
            await self.coordinator.async_set_sim_profile_source(option)
