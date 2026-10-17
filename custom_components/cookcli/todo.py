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
from .shopping import ingredient_summary


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CookCLI todo entities."""
    coordinator: CookCLICoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CookCLIShoppingListTodo(coordinator, entry),
            CookCLIIngredientsTodo(coordinator, entry),
        ]
    )


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


def _ingredient_uid(ingredient: dict) -> str:
    """The same ingredient can be on the list required and optional."""
    prefix = "optional:" if ingredient["optional"] else ""
    return f"{prefix}{ingredient['name'].lower()}"


class CookCLIIngredientsTodo(CoordinatorEntity, TodoListEntity):
    """The ingredients to buy for the recipes on the shopping list.

    Ticking one off here ticks it off in CookCLI too, and the other way round.
    """

    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM
    _attr_icon = "mdi:basket-outline"

    def __init__(self, coordinator: CookCLICoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_shopping_ingredients"
        self._attr_name = "CookCLI Shopping Ingredients"

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=_ingredient_uid(ingredient),
                summary=ingredient_summary(ingredient),
                description=(
                    "optional" if ingredient["optional"] else None
                ),
                status=(
                    TodoItemStatus.COMPLETED
                    if ingredient["checked"]
                    else TodoItemStatus.NEEDS_ACTION
                ),
            )
            for ingredient in self.coordinator.data.get("shopping_ingredients", [])
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Tick an ingredient off, or back on, in CookCLI."""
        ingredient = next(
            (
                i
                for i in self.coordinator.data.get("shopping_ingredients", [])
                if _ingredient_uid(i) == item.uid
            ),
            None,
        )
        if ingredient is None:
            return
        checked = item.status == TodoItemStatus.COMPLETED
        if checked:
            await self.coordinator.api.async_check_ingredient(ingredient["name"])
        else:
            await self.coordinator.api.async_uncheck_ingredient(ingredient["name"])
        # Shown straight away: refreshes are debounced, so ticking off a few
        # items in a row would otherwise flick them back until the next one.
        ingredient["checked"] = checked
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
