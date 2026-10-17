"""CookCLI integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .const import DOMAIN
from .coordinator import CookCLICoordinator
from .shopping import ingredient_summary

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

    async def handle_export(call: ServiceCall) -> dict:
        """Handle export_shopping_list service call."""
        target = call.data["entity_id"]
        await coordinator.async_refresh()
        ingredients = [
            i
            for i in coordinator.data.get("shopping_ingredients", [])
            if not i["checked"] and not i["optional"]
        ]

        # Leave out what is already on the target list and not bought yet, so
        # pressing the button twice does not add everything twice.
        existing = await hass.services.async_call(
            "todo",
            "get_items",
            {"status": ["needs_action"]},
            target={"entity_id": target},
            blocking=True,
            return_response=True,
        )
        on_list = [
            item["summary"].strip().lower()
            for item in existing.get(target, {}).get("items", [])
        ]

        added = []
        for ingredient in ingredients:
            name = ingredient["name"].lower()
            if any(s == name or s.startswith(f"{name} (") for s in on_list):
                continue
            summary = (
                ingredient_summary(ingredient)
                if call.data.get("include_quantities", True)
                else ingredient["name"]
            )
            await hass.services.async_call(
                "todo",
                "add_item",
                {"item": summary},
                target={"entity_id": target},
                blocking=True,
            )
            added.append(summary)
        return {"added": added, "skipped": len(ingredients) - len(added)}

    hass.services.async_register(
        DOMAIN, "search_recipe", handle_search,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "add_recipe_to_shopping_list", handle_add_recipe
    )
    hass.services.async_register(DOMAIN, "clear_shopping_list", handle_clear)
    hass.services.async_register(
        DOMAIN, "export_shopping_list", handle_export,
        supports_response=SupportsResponse.OPTIONAL,
    )

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
            hass.services.async_remove(DOMAIN, "export_shopping_list")
    return unload_ok
