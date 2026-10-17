# CookCLI for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A [Home Assistant](https://www.home-assistant.io/) custom component for [CookCLI](https://cooklang.org/cli/) — the command-line tool for managing [Cooklang](https://cooklang.org/) recipes.

Browse recipes, track your pantry, manage shopping lists, and plan meals — all from your Home Assistant dashboard.

## Features

- **Meal Plan Calendar** — `.menu` files mapped to HA calendar events with per-meal times
- **Shopping List** — the recipes on it, and the ingredients to buy, as HA To-do lists; tick ingredients off in either place
- **Export to HA's Shopping List** — one button copies the ingredients into any HA to-do list
- **Pantry Alerts** — sensors for expiring and depleted items
- **Recipe Stats** — total recipe and menu counts
- **Services** — search recipes, add to shopping list from automations

## Requirements

- Home Assistant 2024.1+
- [CookCLI](https://cooklang.org/cli/) server running (`cook server ./recipes`)

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/cooklang/homeassistant-cookcli` as an **Integration**
4. Search for "CookCLI" and install
5. Restart Home Assistant

### Manual

Copy `custom_components/cookcli/` to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **CookCLI**
3. Enter your CookCLI server URL (default: `http://localhost:9080`)
4. Optionally set an active menu plan file for calendar integration

## Entities

| Entity | Type | Description |
|---|---|---|
| `sensor.cookcli_recipes` | Sensor | Total recipe count (menu count as attribute) |
| `sensor.cookcli_pantry_expiring` | Sensor | Number of items expiring within 7 days |
| `sensor.cookcli_pantry_depleted` | Sensor | Number of low-stock items |
| `todo.cookcli_shopping_list` | Todo | Recipes on the shopping list, with delete support |
| `todo.cookcli_shopping_ingredients` | Todo | Ingredients to buy for those recipes (pantry already subtracted); ticking one off ticks it off in CookCLI |
| `calendar.cookcli_meal_plan` | Calendar | Meal plan from active `.menu` file |

## Calendar: Menu File Format

The calendar entity reads `.menu` files. Sections with dates in parentheses are mapped to calendar days:

```
---
servings: 2
---

== Monday (2026-03-09) ==

Breakfast (08:00): \
- @./Breakfast/Easy Pancakes{10%servings}

Dinner: \
- @./Neapolitan Pizza{}

== Wednesday (2026-03-11) ==

Lunch (12:30): \
- @./Sicilian-style Scottadito Lamb Chops{}

Snack: \
- @crackers{1%box} with @hummus{1%cup}

== Extras ==
- @soy sauce{1%tbsp}
```

- **Section dates** extracted via regex from `== Name (YYYY-MM-DD) ==`
- **Meal times** extracted from headers like `Breakfast (08:30):`
- **Default times** when not specified: Breakfast 07:00, Lunch 12:00, Dinner 18:00, Snack 15:00
- **Sections without dates** (like `== Extras ==`) are ignored for calendar but included in shopping lists

## Services

### `cookcli.search_recipe`

Search recipes by keyword. Returns results as a response variable.

```yaml
service: cookcli.search_recipe
data:
  query: "pasta"
```

### `cookcli.add_recipe_to_shopping_list`

Add a recipe to the shopping list with optional scaling.

```yaml
service: cookcli.add_recipe_to_shopping_list
data:
  recipe: "Neapolitan Pizza.cook"
  scale: 2
```

### `cookcli.clear_shopping_list`

Remove all items from the shopping list.

```yaml
service: cookcli.clear_shopping_list
```

### `cookcli.export_shopping_list`

Copy the ingredients still to buy into another to-do list — for example Home
Assistant's own Shopping List. Ingredients already ticked off in CookCLI, and
ones already on the target list and not yet bought, are left out, so running it
twice doesn't add everything twice. Optional ingredients are only included once
you've chosen them in CookCLI.

```yaml
service: cookcli.export_shopping_list
data:
  entity_id: todo.shopping_list
  include_quantities: true   # "pasta (400 g)" rather than "pasta"
```

A dashboard button for it:

```yaml
type: button
name: Send to shopping list
icon: mdi:cart-arrow-right
tap_action:
  action: perform-action
  perform_action: cookcli.export_shopping_list
  data:
    entity_id: todo.shopping_list
```

## Automation Examples

**Morning meal notification:**
```yaml
automation:
  - alias: "Morning Meal Brief"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Today's Meals"
          message: "Check your CookCLI meal plan"
```

**Pantry expiration alert:**
```yaml
automation:
  - alias: "Pantry Expiration Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.cookcli_pantry_expiring
        above: 0
    action:
      - service: notify.mobile_app
        data:
          title: "Pantry Alert"
          message: >
            {{ state_attr('sensor.cookcli_pantry_expiring', 'items') | length }}
            items expiring soon
```

## Development

The integration polls CookCLI's REST API every 5 minutes via a DataUpdateCoordinator. The CookCLI server needs these API endpoints (available in CookCLI 0.25+):

- `GET /api/stats`
- `GET /api/menus`
- `GET /api/menus/{path}`
- `GET /api/pantry/expiring?days=N`
- `GET /api/pantry/depleted`
- `GET /api/shopping_list/items`
- `POST /api/shopping_list` (builds the ingredient list)
- `POST /api/shopping_list/check`, `POST /api/shopping_list/uncheck`
- `POST /api/shopping_list/add`
- `POST /api/shopping_list/remove`
- `POST /api/shopping_list/clear`
- `GET /api/search?q=term`

## License

[MIT](LICENSE)
