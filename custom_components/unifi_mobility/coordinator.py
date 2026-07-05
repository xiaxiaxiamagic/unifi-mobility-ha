"""Data coordinator for UniFi Mobility."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    UnifiMobilityApi,
    UnifiMobilityAuthError,
    UnifiMobilityConnectionError,
    UnifiMobilityError,
)
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLOW_POLL_MULTIPLIER,
    DEFAULT_POLL_CLIENTS,
    CONF_SCAN_INTERVAL,
    CONF_SLOW_POLL_MULTIPLIER,
    CONF_POLL_CLIENTS,
    DOMAIN,
    RPC_DEVICE_INFO,
    RPC_DEVICE_STATUS,
    RPC_INFO_HIGH,
    RPC_INFO_CLIENT,
    RPC_INFO_LOW,
    RPC_INFO_MEDIUM,
    RPC_SHADOW,
    SHADOW_NETWORKS,
    SHADOW_POWERS,
)

_LOGGER = logging.getLogger(__name__)


class UnifiMobilityCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll read-only local UMR status."""

    def __init__(
        self, hass: HomeAssistant, api: UnifiMobilityApi, entry: ConfigEntry
    ) -> None:
        self.entry = entry
        self._cycle = 0
        self._cache: dict[str, Any] = {}
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        fast_methods: dict[str, tuple[str, dict[str, Any]]] = {
            "low": RPC_INFO_LOW,
            "medium": RPC_INFO_MEDIUM,
            "high": RPC_INFO_HIGH,
            "status": RPC_DEVICE_STATUS,
        }
        slow_methods: dict[str, tuple[str, dict[str, Any]]] = {
            "device": (RPC_DEVICE_INFO, {}),
            "networks": (RPC_SHADOW, {"shadow": SHADOW_NETWORKS}),
            "powers": (RPC_SHADOW, {"shadow": SHADOW_POWERS}),
        }
        fast_methods = {name: (method, {}) for name, method in fast_methods.items()}
        if self.entry.options.get(CONF_POLL_CLIENTS, DEFAULT_POLL_CLIENTS):
            slow_methods["clients"] = (RPC_INFO_CLIENT, {})
        multiplier = self.entry.options.get(
            CONF_SLOW_POLL_MULTIPLIER, DEFAULT_SLOW_POLL_MULTIPLIER
        )
        poll_slow = not self._cache or self._cycle % multiplier == 0
        methods = {**fast_methods, **(slow_methods if poll_slow else {})}

        async def fetch(
            name: str, request: tuple[str, dict[str, Any]]
        ) -> tuple[str, Any]:
            method, params = request
            try:
                result = await self.api.async_call(method, params)
                if method == RPC_SHADOW and isinstance(result, dict):
                    result = result.get("data", result)
                return name, result
            except UnifiMobilityAuthError:
                raise
            except UnifiMobilityConnectionError:
                raise
            except UnifiMobilityError as err:
                # Firmware variants do not necessarily expose every dump method.
                _LOGGER.debug("Optional UMR method %s failed: %s", method, err)
                return name, {}

        try:
            results = await asyncio.gather(
                *(fetch(name, request) for name, request in methods.items())
            )
        except UnifiMobilityAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except UnifiMobilityError as err:
            raise UpdateFailed(str(err)) from err

        data = {**self._cache, **dict(results)}
        if not any(data.values()):
            raise UpdateFailed("The router returned no status data")
        self._cache = data
        self._cycle += 1
        return data
