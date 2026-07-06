"""UniFi Mobility integration."""

from __future__ import annotations

import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify

from .api import UnifiMobilityApi, UnifiMobilityConnectionError
from .const import CONF_VERIFY_SSL, DOMAIN, ENTITY_KEYS, PLATFORMS
from .coordinator import UnifiMobilityCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UniFi Mobility from a config entry."""
    api = UnifiMobilityApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_VERIFY_SSL, False),
    )
    coordinator = UnifiMobilityCoordinator(hass, api, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except UnifiMobilityConnectionError as err:
        raise ConfigEntryNotReady from err
    device = coordinator.data.get("device", {})
    stable_id = device.get("mac") or device.get("imei")
    host_identity = entry.data[CONF_HOST].strip().rstrip("/").lower()
    if stable_id and (
        entry.unique_id is None or entry.unique_id.lower() == host_identity
    ):
        hass.config_entries.async_update_entry(entry, unique_id=str(stable_id).lower())
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate only automatically generated legacy entity IDs."""
    if entry.version >= 2:
        return True
    registry = er.async_get(hass)
    base = slugify(entry.title)
    legacy_pattern = re.compile(
        rf"^{re.escape(base)}(?:_\d+|_(?:data_size|duration|plug|lock|power))?$"
    )
    for platform, keys in ENTITY_KEYS.items():
        for key in keys:
            unique_id = f"{entry.unique_id}_{key}"
            entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
            if entity_id is None:
                continue
            object_id = entity_id.split(".", 1)[1]
            if legacy_pattern.fullmatch(object_id):
                desired_id = f"{platform}.{base}_{key}"
                if registry.async_get(desired_id) is not None:
                    continue
                registry.async_update_entity(entity_id, new_entity_id=desired_id)
    hass.config_entries.async_update_entry(entry, version=2)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and entry.runtime_data:
        await entry.runtime_data.api.async_logout()
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options or credentials change."""
    await hass.config_entries.async_reload(entry.entry_id)
