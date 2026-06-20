"""
Healthcare facility adapter using the CMS NPPES NPI Registry.

Counts hospitals, clinics, and health centers registered in a ZIP code.
Uses the free public NPI Registry API (no key required).
API docs: https://npiregistry.cms.hhs.gov/api-page
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_NPPES_URL = "https://npiregistry.cms.hhs.gov/api/"

# Keywords that indicate a genuine healthcare facility (vs. solo practitioner offices)
_FACILITY_KEYWORDS = frozenset([
    "hospital",
    "medical center",
    "health system",
    "health center",
    "urgent care",
    "emergency",
    "clinic",
    "medical group",
    "healthcare",
    "health services",
])


def fetch_healthcare_data(zip_code: str) -> dict | None:
    """
    Return a dict with keys:
        hospital_count, healthcare_access_score
    or None if the API is unavailable.

    Uses NPPES enumeration_type=2 (organizational providers) to count
    healthcare facilities registered in the given ZIP.
    """
    params: dict[str, str] = {
        "version": "2.1",
        "postal_code": zip_code,
        "enumeration_type": "2",  # organizations only
        "limit": "200",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(_NPPES_URL, params=params)

        if resp.status_code != 200:
            logger.warning("NPPES API returned %s for ZIP %s", resp.status_code, zip_code)
            return None

        data = resp.json()
        results: list[dict] = data.get("results") or []
        total_orgs: int = data.get("result_count", len(results))

        facility_count = 0
        for r in results:
            name = (r.get("basic", {}).get("organization_name") or "").lower()
            if any(kw in name for kw in _FACILITY_KEYWORDS):
                facility_count += 1

        # Access score: facility density + total org density
        # Score range 40–100: 15 facilities → ~100
        access_score = round(min(100.0, 40.0 + facility_count * 4.0 + total_orgs * 0.1), 1)

        return {
            "hospital_count": facility_count,
            "healthcare_access_score": access_score,
        }

    except Exception as exc:
        logger.warning("NPPES fetch failed for ZIP %s: %s", zip_code, exc)
        return None
