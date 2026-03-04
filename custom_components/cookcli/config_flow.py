"""Config flow for CookCLI integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CookCLIApi, CookCLIConnectionError
from .const import CONF_ACTIVE_MENU, DEFAULT_URL, DOMAIN


class CookCLIConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CookCLI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL]
            session = async_get_clientsession(self.hass)
            api = CookCLIApi(url, session)

            try:
                await api.async_get_stats()
            except CookCLIConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="CookCLI",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=DEFAULT_URL): str,
                    vol.Optional(CONF_ACTIVE_MENU): str,
                }
            ),
            errors=errors,
        )
