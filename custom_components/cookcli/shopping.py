"""Turn CookCLI's shopping list into ingredients.

Kept free of Home Assistant imports so it can be tested on its own.
"""
from __future__ import annotations


def build_requests(entries: list[dict]) -> list[dict]:
    """Body for `POST /api/shopping_list` from `GET /api/shopping_list/items`.

    Mirrors CookCLI's shopping list page: a menu entry expands into its
    recipes, plus the menu itself with no references so its freehand
    ingredients are included.
    """
    requests: list[dict] = []
    for entry in entries:
        if entry.get("recipes") is not None:
            requests.append(
                {
                    "recipe": entry["path"],
                    "scale": entry.get("scale", 1),
                    "included_references": [],
                }
            )
            requests.extend(_recipe_request(r) for r in entry["recipes"])
        else:
            requests.append(_recipe_request(entry))
    return requests


def _recipe_request(entry: dict) -> dict:
    request = {"recipe": entry["path"], "scale": entry.get("scale", 1)}
    if entry.get("included_references") is not None:
        request["included_references"] = entry["included_references"]
    if entry.get("optional_ingredients"):
        request["optional_ingredients"] = entry["optional_ingredients"]
    return request


def flatten_ingredients(generated: dict) -> list[dict]:
    """Ingredients from a `POST /api/shopping_list` response, in list order."""
    checked = {name.lower() for name in generated.get("checked", [])}
    ingredients = []
    for category in generated.get("categories", []):
        for item in category.get("items", []):
            ingredients.append(
                {
                    "name": item["name"],
                    "quantity": format_quantities(item.get("quantities", [])),
                    "category": category.get("category"),
                    "optional": item.get("optional", False),
                    "checked": item["name"].lower() in checked,
                }
            )
    return ingredients


def ingredient_summary(ingredient: dict) -> str:
    """One line for a shopping list: `pasta (200 g)`."""
    if ingredient["quantity"]:
        return f"{ingredient['name']} ({ingredient['quantity']})"
    return ingredient["name"]


def format_quantities(quantities: list[dict]) -> str:
    """`200 g, 2 tbsp` from CookCLI's quantity components."""
    parts = []
    for quantity in quantities:
        value = _format_value(quantity.get("value"))
        unit = quantity.get("unit")
        part = " ".join(p for p in (value, unit) if p)
        if part:
            parts.append(part)
    return ", ".join(parts)


def _format_value(value: dict | None) -> str:
    if not isinstance(value, dict):
        return ""
    kind = value.get("type")
    if kind == "number":
        return _format_number(value.get("value"))
    if kind == "range":
        inner = value.get("value") or {}
        return f"{_format_number(inner.get('start'))}-{_format_number(inner.get('end'))}"
    if kind == "text":
        return str(value.get("value") or "")
    return ""


def _format_number(number: dict | None) -> str:
    if not isinstance(number, dict):
        return ""
    if number.get("type") == "regular":
        return f"{round(number.get('value', 0), 3):g}"
    if number.get("type") == "fraction":
        fraction = number.get("value") or {}
        whole = fraction.get("whole") or 0
        num = fraction.get("num") or 0
        den = fraction.get("den") or 1
        if whole and num:
            return f"{whole} {num}/{den}"
        if num:
            return f"{num}/{den}"
        return str(whole)
    return ""
