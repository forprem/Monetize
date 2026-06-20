from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIGER_ZCTA_QUERY_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/tigerWMS_Current/MapServer/2/query"
)
_CACHE_TTL = timedelta(hours=24)
_boundary_cache: dict[str, tuple[dict[str, Any] | None, datetime]] = {}
_CACHE_MISS = object()


def _cached_boundary(zip_code: str) -> dict[str, Any] | None | object:
    hit = _boundary_cache.get(zip_code)
    if not hit:
        return _CACHE_MISS

    boundary, ts = hit
    if datetime.now(timezone.utc) - ts < _CACHE_TTL:
        return boundary

    return _CACHE_MISS


def _fetch_boundary_from_api(zip_code: str) -> dict[str, Any] | None:
    params = {
        "where": f"ZCTA5='{zip_code}'",
        "outFields": "ZCTA5,GEOID,NAME",
        "returnGeometry": "true",
        "f": "geojson",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(_TIGER_ZCTA_QUERY_URL, params=params)
        if response.status_code != 200:
            logger.warning(
                "ZIP boundary API returned %s for ZIP %s",
                response.status_code,
                zip_code,
            )
            return None

        payload = response.json()
        if payload.get("type") != "FeatureCollection":
            return None

        features = payload.get("features", [])
        if not features:
            return None

        return {
            "type": "FeatureCollection",
            "features": [features[0]],
        }
    except Exception as exc:
        logger.warning("ZIP boundary API fetch failed for ZIP %s: %s", zip_code, exc)
        return None


def get_zip_boundary(zip_code: str) -> dict[str, Any] | None:
    normalized = str(zip_code).strip()
    if len(normalized) != 5 or not normalized.isdigit():
        return None

    cached = _cached_boundary(normalized)
    if cached is not _CACHE_MISS:
        # `cached is None` means a previous API miss/failure was cached.
        return cached

    boundary = _fetch_boundary_from_api(normalized)
    _boundary_cache[normalized] = (boundary, datetime.now(timezone.utc))
    return boundary
