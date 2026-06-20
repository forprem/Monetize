"""
Demographics and broadband adapter using Census Reporter.

Census Reporter is a free API layer over ACS Census data and does not require
an API key. It exposes ZIP-level (ZCTA) estimates used by this project.
API docs: https://censusreporter.org/developers/
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_CENSUS_REPORTER_BASE = "https://api.censusreporter.org/1.0/data/show/latest"

# Male age-group variable codes (B01001 table)
_AGE_0_17_M = [f"B01001_{i:03d}E" for i in range(3, 7)]    # under-5, 5-9, 10-14, 15-17
_AGE_18_34_M = [f"B01001_{i:03d}E" for i in range(7, 13)]  # 18-19, 20, 21, 22-24, 25-29, 30-34
_AGE_35_64_M = [f"B01001_{i:03d}E" for i in range(13, 20)] # 35-39 … 62-64
_AGE_65_M = [f"B01001_{i:03d}E" for i in range(20, 26)]    # 65-66 … 85+

# Female counterparts
_AGE_0_17_F = [f"B01001_{i:03d}E" for i in range(27, 31)]
_AGE_18_34_F = [f"B01001_{i:03d}E" for i in range(31, 37)]
_AGE_35_64_F = [f"B01001_{i:03d}E" for i in range(37, 44)]
_AGE_65_F = [f"B01001_{i:03d}E" for i in range(44, 50)]

def _load_tables(zip_code: str, table_ids: str) -> dict | None:
    geo_id = f"86000US{zip_code}"
    params = {
        "table_ids": table_ids,
        "geo_ids": geo_id,
    }

    try:
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(_CENSUS_REPORTER_BASE, params=params)
        except httpx.ConnectError:
            # Some enterprise Linux images have incomplete trust stores for
            # specific CDNs; retry insecurely to keep local/dev usable.
            with httpx.Client(timeout=15.0, verify=False) as insecure_client:
                resp = insecure_client.get(_CENSUS_REPORTER_BASE, params=params)

        if resp.status_code != 200:
            logger.warning("Census Reporter returned %s for ZIP %s", resp.status_code, zip_code)
            return None

        payload = resp.json()
        return payload.get("data", {}).get(geo_id)
    except Exception as exc:
        logger.warning("Census Reporter fetch failed for ZIP %s: %s", zip_code, exc)
        return None


def fetch_census_demographics(zip_code: str, api_key: str = "") -> dict | None:
    """
    Return a dict with keys:
        population_total, median_income,
        age_0_17, age_18_34, age_35_64, age_65_plus
    or None if the ZIP is not found or the API is unavailable.
    """
    _ = api_key  # maintained for backward compatibility; not needed by this source
    geo_tables = _load_tables(zip_code, "B01003,B19013,B01001")
    if not geo_tables:
        return None

    pop = geo_tables.get("B01003", {}).get("estimate", {})
    income = geo_tables.get("B19013", {}).get("estimate", {})
    age = geo_tables.get("B01001", {}).get("estimate", {})

    def _ival(data: dict, key: str) -> int:
        try:
            return max(0, int(float(data.get(key, 0) or 0)))
        except (TypeError, ValueError):
            return 0

    median_income = _ival(income, "B19013001")
    def _age_key(k: str) -> str:
        return k.replace("_", "").removesuffix("E")

    return {
        "population_total": _ival(pop, "B01003001"),
        "median_income": median_income if median_income > 0 else 50_000,
        "age_0_17": sum(_ival(age, _age_key(k)) for k in _AGE_0_17_M + _AGE_0_17_F),
        "age_18_34": sum(_ival(age, _age_key(k)) for k in _AGE_18_34_M + _AGE_18_34_F),
        "age_35_64": sum(_ival(age, _age_key(k)) for k in _AGE_35_64_M + _AGE_35_64_F),
        "age_65_plus": sum(_ival(age, _age_key(k)) for k in _AGE_65_M + _AGE_65_F),
    }


def fetch_census_broadband(zip_code: str) -> dict | None:
    """
    Return broadband proxy metrics from Census ACS table B28002.

    Returns a dict with keys:
        avg_download_mbps, avg_upload_mbps, avg_latency_ms,
        consistency_score, provider_count, signal_score
    """
    geo_tables = _load_tables(zip_code, "B28002")
    if not geo_tables:
        return None

    b = geo_tables.get("B28002", {}).get("estimate", {})

    def _val(key: str) -> float:
        try:
            return float(b.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    total_households = max(1.0, _val("B28002001"))
    internet_households = _val("B28002002")
    broadband_households = _val("B28002004")
    no_internet = _val("B28002013")

    internet_rate = max(0.0, min(1.0, internet_households / total_households))
    broadband_rate = max(0.0, min(1.0, broadband_households / total_households))
    no_internet_rate = max(0.0, min(1.0, no_internet / total_households))

    signal_score = round(internet_rate * 45.0 + broadband_rate * 55.0, 1)
    consistency_score = round(min(100.0, broadband_rate * 100.0), 1)

    avg_download_mbps = round(25.0 + broadband_rate * 180.0, 1)
    avg_upload_mbps = round(5.0 + broadband_rate * 45.0, 1)
    avg_latency_ms = round(max(8.0, 40.0 - broadband_rate * 24.0), 1)

    provider_count = max(1, int(round(1 + broadband_rate * 7 - no_internet_rate * 2)))

    return {
        "avg_download_mbps": avg_download_mbps,
        "avg_upload_mbps": avg_upload_mbps,
        "avg_latency_ms": avg_latency_ms,
        "consistency_score": consistency_score,
        "provider_count": provider_count,
        "signal_score": signal_score,
    }
