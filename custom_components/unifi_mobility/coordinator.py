"""Data coordinator for UniFi Mobility."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from random import uniform
from time import monotonic
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    UnifiMobilityApi,
    UnifiMobilityAuthError,
    UnifiMobilityConnectionError,
    UnifiMobilityError,
    UnifiMobilitySslError,
)
from .const import (
    CONF_POLL_CLIENTS,
    CONF_SCAN_INTERVAL,
    CONF_SLOW_POLL_MULTIPLIER,
    DEFAULT_POLL_CLIENTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLOW_POLL_MULTIPLIER,
    DOMAIN,
    RPC_DEVICE_INFO,
    RPC_DEVICE_STATUS,
    RPC_INFO_CLIENT,
    RPC_INFO_HIGH,
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
        self._section_updated: dict[str, float] = {}
        self._method_failures: dict[str, int] = {}
        self._failure_count = 0
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._base_interval = interval
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.api = api

    def section_available(self, section: str) -> bool:
        """Return whether a data section is present and recent enough."""
        if section not in self._cache or section not in self._section_updated:
            return False
        interval = self.update_interval.total_seconds() if self.update_interval else 30
        multiplier = self.entry.options.get(
            CONF_SLOW_POLL_MULTIPLIER, DEFAULT_SLOW_POLL_MULTIPLIER
        )
        slow = section in {"device", "networks", "powers", "clients"}
        max_age = interval * (multiplier * 2 + 1 if slow else 3)
        return monotonic() - self._section_updated[section] <= max_age

    async def async_reconnect(self) -> None:
        """Safely replace the local read-only API session."""
        await self.api.async_logout()
        await self.api.async_login()
        await self.async_request_refresh()

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
        ) -> tuple[str, Any, bool]:
            method, params = request
            try:
                result = await self.api.async_call(method, params)
                if method == RPC_SHADOW and isinstance(result, dict):
                    result = result.get("data", result)
                self._method_failures.pop(method, None)
                ir.async_delete_issue(self.hass, DOMAIN, f"rpc_{method.lower()}")
                return name, result, True
            except UnifiMobilityAuthError:
                raise
            except UnifiMobilityConnectionError:
                raise
            except UnifiMobilityError as err:
                # Firmware variants do not necessarily expose every dump method.
                _LOGGER.debug("Optional UMR method %s failed: %s", method, err)
                failures = self._method_failures.get(method, 0) + 1
                self._method_failures[method] = failures
                if failures >= 5:
                    ir.async_create_issue(
                        self.hass,
                        DOMAIN,
                        f"rpc_{method.lower()}",
                        is_fixable=False,
                        is_persistent=False,
                        severity=ir.IssueSeverity.WARNING,
                        translation_key="rpc_unavailable",
                        translation_placeholders={"method": method},
                    )
                return name, {}, False

        try:
            results = await asyncio.gather(
                *(fetch(name, request) for name, request in methods.items())
            )
        except UnifiMobilityAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except UnifiMobilitySslError as err:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "invalid_ssl",
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="invalid_ssl",
            )
            raise UpdateFailed(str(err)) from err
        except UnifiMobilityError as err:
            self._failure_count += 1
            delay = min(self._base_interval * (2**self._failure_count), 900)
            self.update_interval = timedelta(seconds=delay + uniform(0, delay * 0.1))
            raise UpdateFailed(str(err)) from err

        now = monotonic()
        updates: dict[str, Any] = {}
        for name, result, succeeded in results:
            if succeeded:
                updates[name] = result
                self._section_updated[name] = now
            elif name not in self._cache:
                updates[name] = {}
        data = {**self._cache, **updates}
        if not any(data.values()):
            raise UpdateFailed("The router returned no status data")
        self._cache = data
        self._cycle += 1
        self._failure_count = 0
        self.update_interval = timedelta(
            seconds=self._base_interval + uniform(0, self._base_interval * 0.1)
        )
        ir.async_delete_issue(self.hass, DOMAIN, "invalid_ssl")
        return data
