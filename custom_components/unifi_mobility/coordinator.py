"""Data coordinator for UniFi Mobility."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from random import uniform
from time import monotonic
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
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
    RPC_ACTION,
    RPC_ACTION_CHECK,
    RPC_DEVICE_INFO,
    RPC_DEVICE_STATUS,
    RPC_INFO_CLIENT,
    RPC_INFO_HIGH,
    RPC_INFO_LOW,
    RPC_INFO_MEDIUM,
    RPC_RADIO_CAPABILITY,
    RPC_RADIO_PREFERENCE,
    RPC_RADIO_PREFERENCE_SET,
    RPC_SHADOW,
    RPC_SHADOW_WRITE,
    RPC_SIM_PROFILE,
    RPC_SIM_PROFILE_SET,
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
        self._control_lock = asyncio.Lock()
        self.last_success_time: datetime | None = None
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
        slow = section in {
            "device",
            "networks",
            "powers",
            "clients",
            "locate",
            "radio_capability",
            "radio_preference",
            "sim_profile",
        }
        max_age = interval * (multiplier * 2 + 1 if slow else 3)
        return monotonic() - self._section_updated[section] <= max_age

    def diagnostic_data(self) -> dict[str, Any]:
        """Return non-sensitive polling health information for diagnostics."""
        now = monotonic()
        return {
            "poll_cycle": self._cycle,
            "base_interval_seconds": self._base_interval,
            "current_interval_seconds": (
                self.update_interval.total_seconds() if self.update_interval else None
            ),
            "consecutive_failures": self._failure_count,
            "rpc_failure_counts": dict(self._method_failures),
            "section_age_seconds": {
                section: round(max(now - updated, 0), 1)
                for section, updated in self._section_updated.items()
            },
        }

    async def async_reconnect(self) -> None:
        """Safely replace the local read-only API session."""
        await self.api.async_reconnect()
        await self.async_request_refresh()

    async def async_restart_device(self) -> None:
        """Restart the router through the same action used by the local portal."""
        async with self._control_lock:
            await self.api.async_call(RPC_ACTION, {"action_name": "reboot"})

    async def async_set_locate(self, enabled: bool) -> None:
        """Turn the router locate indicator on or off."""
        await self._async_control_call(
            RPC_ACTION,
            {"action_name": "locate", "locate_on": enabled},
        )

    async def async_set_poe_passthrough(self, enabled: bool) -> None:
        """Set PoE passthrough using the local portal shadow API."""
        await self._async_control_call(
            RPC_SHADOW_WRITE,
            {
                "timestamp": str(int(datetime.now(UTC).timestamp())),
                "shadow": SHADOW_POWERS,
                "section": "poe",
                "update": enabled,
            },
        )

    async def async_set_network_mode(self, option: str) -> None:
        """Select the cellular radio technologies allowed by the modem."""
        modes = {
            "automatic": ["lte", "umts"],
            "lte_only": ["lte"],
            "umts_only": ["umts"],
        }
        if option not in modes:
            raise HomeAssistantError(f"Unsupported cellular mode: {option}")
        await self._async_set_radio_preference(mode=modes[option])

    async def async_set_lte_band(self, option: str) -> None:
        """Select an LTE band while preserving the cellular mode."""
        band = option.removeprefix("B") if option != "AUTO" else "AUTO"
        capability = self._cache.get("radio_capability", {})
        supported = {str(value) for value in capability.get("lte_band", [])}
        if band != "AUTO" and band not in supported:
            raise HomeAssistantError(f"Unsupported LTE band: {option}")
        wcdma_band = {"1": "wcdma-2100", "8": "wcdma-900"}.get(band, "AUTO")
        await self._async_set_radio_preference(lte_band=[band], band=[wcdma_band])

    async def async_set_sim_profile_source(self, option: str) -> None:
        """Switch between the carrier default and current custom APN profile."""
        sources = {"automatic": 1, "custom": 2}
        if option not in sources:
            raise HomeAssistantError(f"Unsupported SIM profile source: {option}")
        profile = self._cache.get("sim_profile", {})
        default = profile.get("default", {})
        current = profile.get("current", {})
        if not isinstance(default, dict) or not isinstance(current, dict):
            raise HomeAssistantError("SIM profile data is unavailable")
        selected = default if option == "automatic" else current
        payload = {**selected, "apn_configuration_source": sources[option]}
        await self._async_control_call(RPC_SIM_PROFILE_SET, payload)

    async def _async_set_radio_preference(
        self,
        *,
        mode: list[str] | None = None,
        lte_band: list[str] | None = None,
        band: list[str] | None = None,
    ) -> None:
        """Update selected radio fields while preserving the remaining fields."""
        current = self._cache.get("radio_preference", {})
        payload = {
            "mode": list(current.get("mode", [])),
            "lte_band": list(current.get("lte_band", ["AUTO"])),
            "band": list(current.get("band", ["AUTO"])),
        }
        if mode is not None:
            payload["mode"] = mode
        if lte_band is not None:
            payload["lte_band"] = lte_band
        if band is not None:
            payload["band"] = band
        await self._async_control_call(RPC_RADIO_PREFERENCE_SET, payload)

    async def _async_control_call(
        self,
        method: str,
        params: dict[str, Any],
    ) -> None:
        """Serialize writes and force a slow-state refresh afterward."""
        async with self._control_lock:
            await self.api.async_call(method, params)
            self._cycle = 0
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
            "locate": (RPC_ACTION_CHECK, {"action_name": "locate"}),
            "radio_capability": (RPC_RADIO_CAPABILITY, {}),
            "radio_preference": (RPC_RADIO_PREFERENCE, {}),
            "sim_profile": (RPC_SIM_PROFILE, {}),
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
        self.last_success_time = datetime.now(UTC)
        return data
