"""Search endpoints.

Ref: https://docs.kalshi.com (search / filters)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyro.rest.client import RestClient


async def get_sports_filters(client: RestClient) -> Any:
    """Get filters by sport. `GET /search/filters_by_sport`.

    Returns sport-based filter metadata for search/discovery.
    """
    return await client.get("/search/filters_by_sport")


async def get_tags_by_categories(client: RestClient) -> Any:
    """Get tags grouped by category. `GET /search/tags_by_categories`.

    Returns tag metadata for search/filtering.
    """
    return await client.get("/search/tags_by_categories")
