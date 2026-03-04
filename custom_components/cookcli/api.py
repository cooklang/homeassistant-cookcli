"""CookCLI REST API client."""
from __future__ import annotations

import asyncio

import aiohttp
import async_timeout


class CookCLIApiError(Exception):
    """Base exception for CookCLI API errors."""


class CookCLIConnectionError(CookCLIApiError):
    """Connection error."""


class CookCLIApi:
    """Client for CookCLI REST API."""

    def __init__(self, url: str, session: aiohttp.ClientSession) -> None:
        self._url = url.rstrip("/")
        self._session = session

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        """Make a GET request."""
        try:
            async with async_timeout.timeout(10):
                resp = await self._session.get(
                    f"{self._url}{path}", params=params
                )
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CookCLIConnectionError(
                f"Error communicating with CookCLI: {err}"
            ) from err

    async def _post(self, path: str, data: dict | None = None) -> None:
        """Make a POST request."""
        try:
            async with async_timeout.timeout(10):
                resp = await self._session.post(
                    f"{self._url}{path}", json=data
                )
                resp.raise_for_status()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CookCLIConnectionError(
                f"Error communicating with CookCLI: {err}"
            ) from err

    async def async_get_stats(self) -> dict:
        """Get recipe and menu statistics."""
        return await self._get("/api/stats")

    async def async_get_menus(self) -> list[dict]:
        """List all menu files."""
        return await self._get("/api/menus")

    async def async_get_menu(self, path: str) -> dict:
        """Get parsed menu with sections and meals."""
        return await self._get(f"/api/menus/{path}")

    async def async_get_shopping_list_items(self) -> list[dict]:
        """Get current shopping list items."""
        return await self._get("/api/shopping_list/items")

    async def async_add_to_shopping_list(
        self, path: str, name: str, scale: float = 1.0
    ) -> None:
        """Add a recipe to the shopping list."""
        await self._post(
            "/api/shopping_list/add",
            {"path": path, "name": name, "scale": scale},
        )

    async def async_remove_from_shopping_list(self, path: str) -> None:
        """Remove an item from the shopping list."""
        await self._post("/api/shopping_list/remove", {"path": path})

    async def async_clear_shopping_list(self) -> None:
        """Clear the shopping list."""
        await self._post("/api/shopping_list/clear")

    async def async_get_pantry_expiring(self, days: int = 7) -> list[dict]:
        """Get expiring pantry items."""
        return await self._get("/api/pantry/expiring", params={"days": days})

    async def async_get_pantry_depleted(self) -> list[dict]:
        """Get depleted pantry items."""
        return await self._get("/api/pantry/depleted")

    async def async_search(self, query: str) -> list[dict]:
        """Search recipes."""
        return await self._get("/api/search", params={"q": query})
