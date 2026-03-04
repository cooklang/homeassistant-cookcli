"""CookCLI integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .const import DOMAIN
from .coordinator import CookCLICoordinator

PLATFORMS = [Platform.CALENDAR, Platform.TODO, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CookCLI from a config entry."""
    coordinator = CookCLICoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_search(call: ServiceCall) -> dict:
        """Handle search_recipe service call."""
        query = call.data["query"]
        results = await coordinator.api.async_search(query)
        return {"results": results}

    async def handle_add_recipe(call: ServiceCall) -> None:
        """Handle add_recipe_to_shopping_list service call."""
        recipe = call.data["recipe"]
        scale = call.data.get("scale", 1)
        await coordinator.api.async_add_to_shopping_list(recipe, recipe, scale)
        await coordinator.async_request_refresh()

    async def handle_clear(call: ServiceCall) -> None:
        """Handle clear_shopping_list service call."""
        await coordinator.api.async_clear_shopping_list()
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "search_recipe", handle_search,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "add_recipe_to_shopping_list", handle_add_recipe
    )
    hass.services.async_register(DOMAIN, "clear_shopping_list", handle_clear)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "search_recipe")
            hass.services.async_remove(DOMAIN, "add_recipe_to_shopping_list")
            hass.services.async_remove(DOMAIN, "clear_shopping_list")
    return unload_ok
