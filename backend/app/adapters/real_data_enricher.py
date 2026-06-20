"""
Real-data enricher: orchestrates Census, FCC, and NPPES adapters to build
a ZipSummary from live public APIs for any US ZIP code.

Results are cached in-process for 24 hours to avoid redundant API calls.
The API calls are parallelised using a thread pool.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from app.adapters.cdc_places import fetch_places_chronic_data
from app.adapters.census_api import fetch_census_broadband, fetch_census_demographics
from app.adapters.contracts import ZipSummary
from app.adapters.hrsa_health import fetch_healthcare_data
from app.adapters.real_estate import fetch_real_estate_data

logger = logging.getLogger(__name__)

_CACHE_TTL = timedelta(hours=24)
_cache: dict[str, tuple[ZipSummary, datetime]] = {}


def _compute_derived_scores(
    signal_score: float,
    healthcare_access_score: float,
    median_income: int,
    provider_count: int,
) -> tuple[float, float, float]:
    """Return (market_attractiveness, network_opportunity, overall) scores."""
    income_norm = min(1.0, median_income / 150_000)
    market_attractiveness = round(
        signal_score * 0.30
        + healthcare_access_score * 0.20
        + income_norm * 100 * 0.50,
        1,
    )
    network_opportunity = round(
        max(0.0, 100.0 - signal_score) * 0.60
        + max(0.0, 100.0 - min(100.0, provider_count * 12.5)) * 0.40,
        1,
    )
    overall = round(
        signal_score * 0.35
        + healthcare_access_score * 0.25
        + market_attractiveness * 0.40,
        1,
    )
    return market_attractiveness, network_opportunity, overall


def fetch_real_zip_summary(zip_code: str, census_api_key: str = "") -> ZipSummary | None:
    """
    Fetch a ZipSummary for *zip_code* from live public APIs.

    Returns None only if every API call fails (network down, unknown ZIP, etc.).
    Partial failures are tolerated — any available data is merged with safe defaults.
    Results are cached for 24 hours.
    """
    # --- cache hit ---
    cached = _cache.get(zip_code)
    if cached:
        summary, ts = cached
        if datetime.now(timezone.utc) - ts < _CACHE_TTL:
            return summary

    # --- parallel fetch ---
    with ThreadPoolExecutor(max_workers=5) as pool:
        fut_census = pool.submit(fetch_census_demographics, zip_code, census_api_key)
        fut_broadband = pool.submit(fetch_census_broadband, zip_code)
        fut_health = pool.submit(fetch_healthcare_data, zip_code)
        fut_realestate = pool.submit(fetch_real_estate_data, zip_code, census_api_key)
        fut_chronic = pool.submit(fetch_places_chronic_data, zip_code)

        census_data: dict | None = None
        health_data: dict | None = None
        broadband_data: dict | None = None
        realestate_data: dict | None = None
        chronic_data: dict | None = None

        try:
            census_data = fut_census.result()
        except Exception as exc:
            logger.warning("Census future failed for ZIP %s: %s", zip_code, exc)

        try:
            health_data = fut_health.result()
        except Exception as exc:
            logger.warning("Health future failed for ZIP %s: %s", zip_code, exc)

        try:
            broadband_data = fut_broadband.result()
        except Exception as exc:
            logger.warning("Broadband future failed for ZIP %s: %s", zip_code, exc)

        try:
            realestate_data = fut_realestate.result()
        except Exception as exc:
            logger.warning("Real estate future failed for ZIP %s: %s", zip_code, exc)

        try:
            chronic_data = fut_chronic.result()
        except Exception as exc:
            logger.warning("CDC chronic-data future failed for ZIP %s: %s", zip_code, exc)

    # Require core ZIP-level evidence from Census demographics or broadband.
    # Healthcare-only hits can occur for low-quality/invalid ZIP inputs.
    if not any([census_data, broadband_data]):
        logger.warning("Core real-data APIs failed for ZIP %s", zip_code)
        return None

    # --- merge with safe defaults ---
    c = census_data or {}
    h = health_data or {}
    b = broadband_data or {}
    r = realestate_data or {}
    p = chronic_data or {}

    population_total = c.get("population_total") or 10_000
    median_income = c.get("median_income") or 55_000
    age_0_17 = c.get("age_0_17", 0)
    age_18_34 = c.get("age_18_34", 0)
    age_35_64 = c.get("age_35_64", 0)
    age_65_plus = c.get("age_65_plus", 0)

    hospital_count = h.get("hospital_count", 0)
    healthcare_access_score = h.get("healthcare_access_score", 50.0)

    avg_download_mbps = b.get("avg_download_mbps", 50.0)
    avg_upload_mbps = b.get("avg_upload_mbps", 10.0)
    avg_latency_ms = b.get("avg_latency_ms", 25.0)
    consistency_score = b.get("consistency_score", 60.0)
    provider_count = b.get("provider_count", 2)
    signal_score = b.get("signal_score", 60.0)

    home_ownership_rate = r.get("home_ownership_rate", 65.0)
    vacancy_rate = r.get("vacancy_rate", 10.0)
    median_home_value = r.get("median_home_value", 350_000)
    avg_household_size = r.get("avg_household_size", 2.5)

    market_attractiveness, network_opportunity, overall = _compute_derived_scores(
        signal_score, healthcare_access_score, median_income, provider_count
    )

    summary = ZipSummary(
        zip_code=zip_code,
        signal_score=signal_score,
        avg_download_mbps=avg_download_mbps,
        avg_upload_mbps=avg_upload_mbps,
        avg_latency_ms=avg_latency_ms,
        consistency_score=consistency_score,
        provider_count=provider_count,
        hospital_count=hospital_count,
        healthcare_access_score=healthcare_access_score,
        population_total=population_total,
        median_income=median_income,
        age_0_17=age_0_17,
        age_18_34=age_18_34,
        age_35_64=age_35_64,
        age_65_plus=age_65_plus,
        network_opportunity_score=network_opportunity,
        market_attractiveness_score=market_attractiveness,
        overall_score=overall,
        home_ownership_rate=home_ownership_rate,
        vacancy_rate=vacancy_rate,
        median_home_value=median_home_value,
        avg_household_size=avg_household_size,
        updated_at=datetime.now(timezone.utc),
    )

    # Optional CDC PLACES fields are attached dynamically to keep the core
    # storage contract stable while still returning richer API responses.
    for key, value in p.items():
        setattr(summary, key, value)

    _cache[zip_code] = (summary, datetime.now(timezone.utc))
    return summary
