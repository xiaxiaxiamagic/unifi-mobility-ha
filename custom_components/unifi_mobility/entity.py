"""Base entity for UniFi Mobility."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UnifiMobilityCoordinator


class UnifiMobilityEntity(CoordinatorEntity[UnifiMobilityCoordinator]):
    """Base coordinated UMR entity."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: UnifiMobilityCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        device = coordinator.data.get("device", {})
        identity = entry.unique_id or device.get("mac") or device.get("imei")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(identity))},
            name=entry.title,
            manufacturer="Ubiquiti",
            model=device.get("model_name") or "UniFi Mobile Router",
            serial_number=device.get("imei"),
            sw_version=coordinator.data.get("low", {}).get("fw"),
            configuration_url=(
                entry.data["host"]
                if entry.data["host"].startswith(("http://", "https://"))
                else f"https://{entry.data['host']}"
            ),
        )
        self._identity = str(identity)
