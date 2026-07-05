"""UniFi Mobility integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import UnifiMobilityApi, UnifiMobilityConnectionError
from .const import CONF_VERIFY_SSL, PLATFORMS
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
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
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
