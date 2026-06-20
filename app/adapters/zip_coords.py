from __future__ import annotations

from functools import lru_cache
from math import isnan

import pgeocode


@lru_cache(maxsize=1)
def _zip_locator() -> pgeocode.Nominatim:
    return pgeocode.Nominatim("us")


def _normalize_zip(zip_code: str) -> str:
    digits = "".join(char for char in zip_code if char.isdigit())
    return digits[:5]


@lru_cache(maxsize=10000)
def resolve_zip_coordinates(zip_code: str) -> tuple[float, float] | None:
    normalized = _normalize_zip(zip_code)
    if len(normalized) != 5:
        return None

    result = _zip_locator().query_postal_code(normalized)
    latitude = getattr(result, "latitude", None)
    longitude = getattr(result, "longitude", None)

    if latitude is None or longitude is None:
        return None

    lat = float(latitude)
    lon = float(longitude)
    if isnan(lat) or isnan(lon):
        return None

    return lat, lon