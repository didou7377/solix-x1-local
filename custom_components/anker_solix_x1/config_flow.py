"""Config flow for Anker Solix X1."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODBUS_TIMEOUT,
)

_SCAN_INTERVAL_VALIDATOR = vol.All(vol.Coerce(int), vol.Range(min=1, max=3600))


async def _can_connect(host: str, port: int) -> bool:
    """Validate Modbus TCP connectivity."""
    client = AsyncModbusTcpClient(host=host, port=port, timeout=MODBUS_TIMEOUT, retries=0)
    try:
        return await client.connect()
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        return False
    finally:
        client.close()


class AnkerSolixX1ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Anker Solix X1."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            if await _can_connect(user_input[CONF_HOST], user_input[CONF_PORT]):
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): _SCAN_INTERVAL_VALIDATOR,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AnkerSolixX1OptionsFlow:
        """Return the options flow."""
        return AnkerSolixX1OptionsFlow()


class AnkerSolixX1OptionsFlow(OptionsFlow):
    """Options flow for Anker Solix X1."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        schema = vol.Schema(
            {vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): _SCAN_INTERVAL_VALIDATOR}
        )

        return self.async_show_form(step_id="init", data_schema=schema)
