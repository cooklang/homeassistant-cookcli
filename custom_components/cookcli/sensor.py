"""Sensor entities for CookCLI."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    """Set up CookCLI sensors."""
    coordinator: CookCLICoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        CookCLIRecipeCountSensor(coordinator, entry),
        CookCLIPantryExpiringSensor(coordinator, entry),
        CookCLIPantryDepletedSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class CookCLIRecipeCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing total recipe count."""

    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator: CookCLICoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_recipe_count"
        self._attr_name = "CookCLI Recipes"

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("stats")
        if stats:
            return stats.get("recipe_count")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        stats = self.coordinator.data.get("stats", {})
        return {"menu_count": stats.get("menu_count", 0)}


class CookCLIPantryExpiringSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing number of expiring pantry items."""

    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, coordinator: CookCLICoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pantry_expiring"
        self._attr_name = "CookCLI Pantry Expiring"

    @property
    def native_value(self) -> int:
        items = self.coordinator.data.get("pantry_expiring", [])
        return len(items)

    @property
    def extra_state_attributes(self) -> dict:
        return {"items": self.coordinator.data.get("pantry_expiring", [])}


class CookCLIPantryDepletedSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing number of depleted pantry items."""

    _attr_icon = "mdi:basket-off-outline"

    def __init__(self, coordinator: CookCLICoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pantry_depleted"
        self._attr_name = "CookCLI Pantry Depleted"

    @property
    def native_value(self) -> int:
        items = self.coordinator.data.get("pantry_depleted", [])
        return len(items)

    @property
    def extra_state_attributes(self) -> dict:
        return {"items": self.coordinator.data.get("pantry_depleted", [])}
