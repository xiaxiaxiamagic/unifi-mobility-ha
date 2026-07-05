"""Config flow for UniFi Mobility."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    UnifiMobilityApi,
    UnifiMobilityAuthError,
    UnifiMobilityConnectionError,
    UnifiMobilityError,
)
from .const import (
    CONF_POLL_CLIENTS,
    CONF_SCAN_INTERVAL,
    CONF_SLOW_POLL_MULTIPLIER,
    CONF_VERIFY_SSL,
    DEFAULT_POLL_CLIENTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLOW_POLL_MULTIPLIER,
    DOMAIN,
    RPC_DEVICE_INFO,
    RPC_INFO_LOW,
)


class UnifiMobilityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a local UMR."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return UnifiMobilityOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            api = UnifiMobilityApi(
                async_get_clientsession(self.hass),
                host,
                user_input[CONF_PASSWORD],
                user_input[CONF_VERIFY_SSL],
            )
            try:
                await api.async_login()
                low = await api.async_call(RPC_INFO_LOW)
                try:
                    device = await api.async_call(RPC_DEVICE_INFO)
                except UnifiMobilityError:
                    device = {}
            except UnifiMobilityAuthError:
                errors["base"] = "invalid_auth"
            except UnifiMobilityConnectionError:
                errors["base"] = "cannot_connect"
            except UnifiMobilityError:
                errors["base"] = "unknown"
            else:
                identity = device.get("mac") or device.get("imei") or host
                await self.async_set_unique_id(str(identity).lower())
                self._abort_if_unique_id_configured()
                title = (
                    device.get("name")
                    or device.get("model_name")
                    or "UniFi Mobile Router"
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                    description_placeholders={"firmware": str(low.get("fw", ""))},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.105.1"): str,
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_VERIFY_SSL, default=False): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Start reauthentication after the device rejects credentials."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**self._reauth_entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            api = UnifiMobilityApi(
                async_get_clientsession(self.hass),
                data[CONF_HOST],
                data[CONF_PASSWORD],
                data.get(CONF_VERIFY_SSL, False),
            )
            try:
                await api.async_login()
            except UnifiMobilityAuthError:
                errors["base"] = "invalid_auth"
            except UnifiMobilityError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=data
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    )
                }
            ),
            errors=errors,
        )


class UnifiMobilityOptionsFlow(config_entries.OptionsFlow):
    """Change connection and polling settings."""

    def __init__(self, entry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                **self.entry.data,
                CONF_HOST: user_input[CONF_HOST].strip().rstrip("/"),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
            }
            api = UnifiMobilityApi(
                async_get_clientsession(self.hass),
                data[CONF_HOST],
                data[CONF_PASSWORD],
                data[CONF_VERIFY_SSL],
            )
            try:
                await api.async_login()
            except UnifiMobilityAuthError:
                errors["base"] = "invalid_auth"
            except UnifiMobilityError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(self.entry, data=data)
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_SLOW_POLL_MULTIPLIER: user_input[
                            CONF_SLOW_POLL_MULTIPLIER
                        ],
                        CONF_POLL_CLIENTS: user_input[CONF_POLL_CLIENTS],
                    },
                )
        options = self.entry.options
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=self.entry.data[CONF_HOST]): str,
                vol.Required(
                    CONF_PASSWORD, default=self.entry.data[CONF_PASSWORD]
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_VERIFY_SSL,
                    default=self.entry.data.get(CONF_VERIFY_SSL, False),
                ): bool,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=15, max=300)),
                vol.Required(
                    CONF_SLOW_POLL_MULTIPLIER,
                    default=options.get(
                        CONF_SLOW_POLL_MULTIPLIER,
                        DEFAULT_SLOW_POLL_MULTIPLIER,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=2, max=60)),
                vol.Required(
                    CONF_POLL_CLIENTS,
                    default=options.get(CONF_POLL_CLIENTS, DEFAULT_POLL_CLIENTS),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
