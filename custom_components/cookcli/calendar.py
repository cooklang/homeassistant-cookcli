"""Calendar entity for CookCLI menu meal plans."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MEAL_TIMES, DOMAIN
from .coordinator import CookCLICoordinator

DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")
TIME_RE = re.compile(r"\((\d{2}:\d{2})\)")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CookCLI calendar entities."""
    coordinator: CookCLICoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.active_menu:
        async_add_entities([CookCLIMealPlanCalendar(coordinator, entry)])


class CookCLIMealPlanCalendar(CoordinatorEntity, CalendarEntity):
    """Meal plan calendar from a .menu file."""

    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(self, coordinator: CookCLICoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_meal_plan"
        self._attr_name = "CookCLI Meal Plan"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = datetime.now()
        events = self._parse_events()
        future = [e for e in events if e.end > now]
        return future[0] if future else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events in a date range."""
        events = self._parse_events()
        return [
            e
            for e in events
            if e.start < end_date and e.end > start_date
        ]

    def _parse_events(self) -> list[CalendarEvent]:
        """Parse menu data into calendar events."""
        menu = self.coordinator.data.get("menu")
        if not menu:
            return []

        events = []
        for section in menu.get("sections", []):
            section_name = section.get("name") or ""
            date_match = DATE_RE.search(section_name)
            if not date_match:
                continue

            date_str = date_match.group(1)

            for meal in section.get("meals", []):
                meal_type = meal.get("type", "Meal")
                time_str = meal.get("time")

                if not time_str:
                    time_str = DEFAULT_MEAL_TIMES.get(meal_type.lower())

                descriptions = []
                for item in meal.get("items", []):
                    if item.get("kind") == "recipe_reference":
                        descriptions.append(item["name"])
                    elif item.get("kind") == "ingredient":
                        descriptions.append(item["name"])
                description = ", ".join(descriptions)

                if time_str:
                    start = datetime.fromisoformat(f"{date_str}T{time_str}")
                    end = start + timedelta(hours=1)
                else:
                    start = datetime.fromisoformat(f"{date_str}T00:00")
                    end = start + timedelta(days=1)

                events.append(
                    CalendarEvent(
                        summary=meal_type,
                        description=description,
                        start=start,
                        end=end,
                    )
                )

        return sorted(events, key=lambda e: e.start)
