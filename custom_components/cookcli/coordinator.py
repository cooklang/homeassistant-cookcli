"""DataUpdateCoordinator for CookCLI."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CookCLIApi, CookCLIApiError
from .const import CONF_ACTIVE_MENU, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CookCLICoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for polling CookCLI API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        session = async_get_clientsession(hass)
        self.api = CookCLIApi(entry.data[CONF_URL], session)
        self.active_menu: str | None = entry.data.get(CONF_ACTIVE_MENU)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from CookCLI."""
        try:
            stats = await self.api.async_get_stats()
            shopping_items = await self.api.async_get_shopping_list_items()
            pantry_expiring = await self.api.async_get_pantry_expiring(days=7)
            pantry_depleted = await self.api.async_get_pantry_depleted()

            menu = None
            if self.active_menu:
                menu = await self.api.async_get_menu(self.active_menu)

            return {
                "stats": stats,
                "shopping_items": shopping_items,
                "pantry_expiring": pantry_expiring,
                "pantry_depleted": pantry_depleted,
                "menu": menu,
            }
        except CookCLIApiError as err:
            raise UpdateFailed(f"Error fetching CookCLI data: {err}") from err
