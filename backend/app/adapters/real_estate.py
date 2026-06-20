"""
Real estate housing adapter using Census Reporter.

Fetches housing metrics including ownership rate, vacancy rate,
median home value, and household size from Census ACS data.
"""
from __future__ import annotations

import logging

from app.adapters.census_api import _load_tables

logger = logging.getLogger(__name__)


def fetch_real_estate_data(zip_code: str, api_key: str = "") -> dict | None:
    """
    Return a dict with keys:
        home_ownership_rate (0-100),
        vacancy_rate (0-100),
        median_home_value (dollars),
        avg_household_size (persons per unit)
    or None if the ZIP is not found or the API is unavailable.
    
    Uses Census tables:
    - B25003: Tenure (Owner vs Renter occupied)
    - B25002: Occupancy Status (Occupied vs Vacant)
    - B25097: Median Home Value
    - B25010: Average Household Size
    """
    _ = api_key  # maintained for backward compatibility
    
    geo_tables = _load_tables(zip_code, "B25003,B25002,B25097,B25010")
    if not geo_tables:
        return None

    tenure = geo_tables.get("B25003", {}).get("estimate", {})
    occupancy = geo_tables.get("B25002", {}).get("estimate", {})
    home_value = geo_tables.get("B25097", {}).get("estimate", {})
    household_size = geo_tables.get("B25010", {}).get("estimate", {})

    def _ival(data: dict, key: str) -> int:
        try:
            return max(0, int(float(data.get(key, 0) or 0)))
        except (TypeError, ValueError):
            return 0

    def _fval(data: dict, key: str) -> float:
        try:
            return max(0.0, float(data.get(key, 0) or 0))
        except (TypeError, ValueError):
            return 0.0

    # Calculate ownership rate
    owner_occupied = _ival(tenure, "B25003002")  # Owner-occupied
    renter_occupied = _ival(tenure, "B25003003")  # Renter-occupied
    total_occupied = owner_occupied + renter_occupied

    ownership_rate = round((owner_occupied / total_occupied * 100) if total_occupied > 0 else 0, 1)

    # Calculate vacancy rate
    occupied = _ival(occupancy, "B25002002")  # Occupied
    vacant = _ival(occupancy, "B25002003")    # Vacant
    total_units = occupied + vacant

    vacancy_rate = round((vacant / total_units * 100) if total_units > 0 else 0, 1)

    # Median home value (for owner-occupied units)
    median_value = _ival(home_value, "B25097001")

    # Average household size
    avg_hh_size = round(_fval(household_size, "B25010001"), 2)

    return {
        "home_ownership_rate": ownership_rate,
        "vacancy_rate": vacancy_rate,
        "median_home_value": median_value,
        "avg_household_size": avg_hh_size,
    }
