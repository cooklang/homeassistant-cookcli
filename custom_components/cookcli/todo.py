"""Todo entity for CookCLI shopping list."""
from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CookCLICoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CookCLI todo entities."""
    coordinator: CookCLICoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CookCLIShoppingListTodo(coordinator, entry)])


class CookCLIShoppingListTodo(CoordinatorEntity, TodoListEntity):
    """Shopping list as a Todo entity."""

    _attr_supported_features = TodoListEntityFeature.DELETE_TODO_ITEM
    _attr_icon = "mdi:cart-outline"

    def __init__(self, coordinator: CookCLICoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_shopping_list"
        self._attr_name = "CookCLI Shopping List"

    @property
    def todo_items(self) -> list[TodoItem]:
        items = self.coordinator.data.get("shopping_items", [])
        return [
            TodoItem(
                uid=f"{item['path']}_{i}",
                summary=(
                    f"{item['name']} (x{item['scale']})"
                    if item.get("scale", 1) != 1
                    else item["name"]
                ),
                status=TodoItemStatus.NEEDS_ACTION,
            )
            for i, item in enumerate(items)
        ]

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Remove items from shopping list."""
        for uid in uids:
            # Extract original path (uid format: "path_index")
            path = uid.rsplit("_", 1)[0]
            await self.coordinator.api.async_remove_from_shopping_list(path)
        await self.coordinator.async_request_refresh()
