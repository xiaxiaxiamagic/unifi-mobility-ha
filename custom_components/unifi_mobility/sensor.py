"""Sensors for UniFi Mobility."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import UnifiMobilityCoordinator
from .entity import UnifiMobilityEntity
from .parser import (
    as_int,
    billing_date,
    data_limit,
    data_remaining,
    data_usage,
    data_usage_percent,
    days_until_billing,
    first,
)


@dataclass(frozen=True, kw_only=True)
class MobilitySensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    section: str | None = None


def path(section: str, *keys: str) -> Callable[[dict[str, Any]], Any]:
    """Build a safe nested value extractor."""

    def get(data: dict[str, Any]) -> Any:
        value: Any = data.get(section, {})
        for key in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value

    return get


SENSORS = (
    MobilitySensorDescription(
        key="firmware",
        translation_key="firmware",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="low",
        value_fn=path("low", "fw"),
    ),
    MobilitySensorDescription(
        key="operator",
        translation_key="operator",
        icon="mdi:access-point-network",
        section="low",
        value_fn=path("low", "geo_isp"),
    ),
    MobilitySensorDescription(
        key="network_source",
        translation_key="network_source",
        icon="mdi:wan",
        section="low",
        value_fn=path("low", "network_source"),
    ),
    MobilitySensorDescription(
        key="lte_band",
        translation_key="lte_band",
        icon="mdi:signal",
        section="status",
        value_fn=path("status", "lte", "band"),
    ),
    MobilitySensorDescription(
        key="rssi",
        translation_key="rssi",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        section="high",
        value_fn=path("high", "rssi"),
    ),
    MobilitySensorDescription(
        key="rsrp",
        translation_key="rsrp",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        section="high",
        value_fn=path("high", "rsrp"),
    ),
    MobilitySensorDescription(
        key="rsrq",
        translation_key="rsrq",
        native_unit_of_measurement="dB",
        state_class=SensorStateClass.MEASUREMENT,
        section="high",
        value_fn=path("high", "rsrq"),
    ),
    MobilitySensorDescription(
        key="cpu",
        translation_key="cpu",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        section="medium",
        value_fn=path("medium", "cpu"),
    ),
    MobilitySensorDescription(
        key="memory",
        translation_key="memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        section="medium",
        value_fn=path("medium", "memory"),
    ),
    MobilitySensorDescription(
        key="data_usage",
        translation_key="data_usage",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.TOTAL,
        section="medium",
        value_fn=data_usage,
    ),
    MobilitySensorDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: (
            d.get("device", {}).get("uptime") or d.get("low", {}).get("uptime")
        ),
    ),
    MobilitySensorDescription(
        key="wan_ip",
        translation_key="wan_ip",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="device",
        value_fn=path("device", "wan_ip"),
    ),
    MobilitySensorDescription(
        key="lan_ip",
        translation_key="lan_ip",
        icon="mdi:ip",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="device",
        value_fn=path("device", "lan_ip"),
    ),
    MobilitySensorDescription(
        key="client_count",
        translation_key="client_count",
        icon="mdi:devices",
        section="clients",
        value_fn=lambda d: sum(
            1 for v in d.get("clients", {}).values() if isinstance(v, dict)
        ),
    ),
    MobilitySensorDescription(
        key="signal_quality",
        translation_key="signal_quality",
        device_class=SensorDeviceClass.ENUM,
        options=["excellent", "good", "fair", "poor", "no_signal"],
        icon="mdi:signal-cellular-3",
        section="high",
        value_fn=lambda d: signal_quality(d.get("high", {}).get("rsrp")),
    ),
    MobilitySensorDescription(
        key="network_type",
        translation_key="network_type",
        icon="mdi:network-strength-4-cog",
        section="status",
        value_fn=lambda d: first(
            d.get("status", {}).get("lte", {}),
            "network_type",
            "rat",
            "access_technology",
            "registration_type",
        ),
    ),
    MobilitySensorDescription(
        key="iccid",
        translation_key="iccid",
        icon="mdi:sim",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        section="low",
        value_fn=path("low", "iccid"),
    ),
    MobilitySensorDescription(
        key="imei",
        translation_key="imei",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        section="device",
        value_fn=path("device", "imei"),
    ),
    MobilitySensorDescription(
        key="lte_model",
        translation_key="lte_model",
        icon="mdi:expansion-card",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="device",
        value_fn=path("device", "lte_model_name"),
    ),
    MobilitySensorDescription(
        key="rx_channel",
        translation_key="rx_channel",
        icon="mdi:download-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="high",
        value_fn=path("high", "rx_channel"),
    ),
    MobilitySensorDescription(
        key="tx_channel",
        translation_key="tx_channel",
        icon="mdi:upload-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="high",
        value_fn=path("high", "tx_channel"),
    ),
    MobilitySensorDescription(
        key="data_limit",
        translation_key="data_limit",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        section="networks",
        value_fn=data_limit,
    ),
    MobilitySensorDescription(
        key="billing_cycle_day",
        translation_key="billing_cycle_day",
        device_class=SensorDeviceClass.DATE,
        section="networks",
        value_fn=lambda d: billing_date(
            d, dt_util.now().date(), dt_util.DEFAULT_TIME_ZONE
        ),
    ),
    MobilitySensorDescription(
        key="wan_ipv6",
        translation_key="wan_ipv6",
        icon="mdi:ip-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="device",
        value_fn=path("device", "wan_ipv6"),
    ),
    MobilitySensorDescription(
        key="data_remaining",
        translation_key="data_remaining",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        section="networks",
        value_fn=data_remaining,
    ),
    MobilitySensorDescription(
        key="data_usage_percent",
        translation_key="data_usage_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        section="networks",
        value_fn=data_usage_percent,
    ),
    MobilitySensorDescription(
        key="days_until_billing",
        translation_key="days_until_billing",
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:calendar-clock",
        section="networks",
        value_fn=lambda d: days_until_billing(
            d, dt_util.now().date(), dt_util.DEFAULT_TIME_ZONE
        ),
    ),
)


def signal_quality(value: Any) -> str:
    try:
        rsrp = float(value)
    except (TypeError, ValueError):
        return "no_signal"
    if rsrp > -80:
        return "excellent"
    if rsrp > -90:
        return "good"
    if rsrp > -100:
        return "fair"
    return "poor"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: UnifiMobilityCoordinator = entry.runtime_data
    async_add_entities(
        MobilitySensor(coordinator, entry, description)
        for description in SENSORS
        if (
            description.section is None
            or coordinator.section_available(description.section)
        )
        and description.value_fn(coordinator.data) is not None
    )


class MobilitySensor(UnifiMobilityEntity, SensorEntity):
    """A UMR sensor."""

    entity_description: MobilitySensorDescription

    def __init__(
        self, coordinator, entry, description: MobilitySensorDescription
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._identity}_{description.key}"
        self._attr_suggested_object_id = (
            f"{self._attr_suggested_object_id}_{description.key}"
        )

    @property
    def native_value(self):
        value = self.entity_description.value_fn(self.coordinator.data)
        if self.entity_description.key in {
            "data_usage",
            "data_limit",
            "data_remaining",
        }:
            return as_int(value)
        return value

    @property
    def available(self) -> bool:
        section = self.entity_description.section
        return super().available and (
            section is None or self.coordinator.section_available(section)
        )
