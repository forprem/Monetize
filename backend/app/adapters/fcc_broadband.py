"""
FCC Broadband Map adapter.

Fetches real broadband/network data per location from the FCC's free public API.
Derives signal_score, speeds, provider_count, consistency_score from availability data.
API docs: https://broadbandmap.fcc.gov/about
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_FCC_BASE = "https://broadbandmap.fcc.gov/api/public/map"

# Technology codes considered high-quality (cable / fiber)
# 40 = Cable Modem DOCSIS 3.0, 41 = Cable Modem Other, 50 = Optical Fiber
_HIGH_QUALITY_TECH = {40, 41, 50}


def fetch_fcc_broadband(lat: float, lon: float) -> dict | None:
    """
    Query the FCC Broadband Map availability API for a lat/lon point.

    Returns a dict with keys:
        avg_download_mbps, avg_upload_mbps, avg_latency_ms,
        consistency_score, provider_count, signal_score
    or None if no data is available or the API is unreachable.
    """
    params: dict = {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "unit": "location",
        "limit": 100,
        "offset": 0,
    }

    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.get(f"{_FCC_BASE}/listAvailability", params=params)

        if resp.status_code != 200:
            logger.warning("FCC API returned %s for lat=%.4f,lon=%.4f", resp.status_code, lat, lon)
            return None

        payload = resp.json()
        providers: list[dict] = payload.get("data") or []
        if not providers:
            return None

        unique_brands: set[str] = set()
        dl_speeds: list[float] = []
        ul_speeds: list[float] = []
        high_quality_count = 0

        for p in providers:
            brand = (
                p.get("brand_name")
                or p.get("doing_business_as_name")
                or "Unknown"
            )
            unique_brands.add(brand)

            dl = float(p.get("max_download_speed") or 0)
            ul = float(p.get("max_upload_speed") or 0)
            if dl > 0:
                dl_speeds.append(dl)
            if ul > 0:
                ul_speeds.append(ul)

            try:
                tech = int(p.get("technology") or 0)
                if tech in _HIGH_QUALITY_TECH:
                    high_quality_count += 1
            except (ValueError, TypeError):
                pass

        provider_count = len(unique_brands)
        avg_dl = round(sum(dl_speeds) / len(dl_speeds), 1) if dl_speeds else 25.0
        avg_ul = round(sum(ul_speeds) / len(ul_speeds), 1) if ul_speeds else 5.0

        # Signal score: blend of average speed and provider availability
        speed_score = min(100.0, avg_dl / 10.0)          # 1 Gbps → 100
        provider_score = min(100.0, provider_count * 12.5) # 8 providers → 100
        signal_score = round(speed_score * 0.6 + provider_score * 0.4, 1)

        # Consistency: more fiber/cable = better consistency
        consistency_score = round(min(98.0, 50.0 + high_quality_count * 8.0), 1)

        # Latency approximation (fiber/cable → lower latency)
        avg_latency_ms = round(max(5.0, 35.0 - provider_count - high_quality_count * 2.0), 1)

        return {
            "avg_download_mbps": avg_dl,
            "avg_upload_mbps": avg_ul,
            "avg_latency_ms": avg_latency_ms,
            "consistency_score": consistency_score,
            "provider_count": provider_count,
            "signal_score": signal_score,
        }

    except Exception as exc:
        logger.warning("FCC fetch failed for lat=%.4f,lon=%.4f: %s", lat, lon, exc)
        return None
