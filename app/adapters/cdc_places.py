"""
CDC PLACES adapter for ZIP (ZCTA) chronic disease prevalence metrics.

Data source (Socrata):
  https://data.cdc.gov/resource/kee5-23sr.json

Returns ZIP-level prevalence percentages and derived burden estimates.
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_PLACES_ZCTA_URL = "https://data.cdc.gov/resource/kee5-23sr.json"


def _fval(row: dict, key: str) -> float | None:
    try:
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        value = float(raw)
        if value < 0:
            return None
        return value
    except (TypeError, ValueError):
        return None


def _ival(row: dict, key: str) -> int | None:
    try:
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        value = int(float(raw))
        if value < 0:
            return None
        return value
    except (TypeError, ValueError):
        return None


def fetch_places_chronic_data(zip_code: str) -> dict | None:
    """Fetch CDC PLACES chronic-disease prevalence metrics for a ZIP code."""
    params = {
        "$limit": 1,
        "zcta5": zip_code,
        "$select": (
            "zcta5,totalpopulation,"
            "diabetes_crudeprev,bphigh_crudeprev,obesity_crudeprev,"
            "chd_crudeprev,copd_crudeprev,stroke_crudeprev"
        ),
    }

    try:
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(_PLACES_ZCTA_URL, params=params)
        except httpx.ConnectError:
            with httpx.Client(timeout=15.0, verify=False) as insecure_client:
                resp = insecure_client.get(_PLACES_ZCTA_URL, params=params)

        if resp.status_code != 200:
            logger.warning("CDC PLACES returned %s for ZIP %s", resp.status_code, zip_code)
            return None

        rows = resp.json()
        if not rows:
            return None

        row = rows[0]
        diabetes = _fval(row, "diabetes_crudeprev")
        hypertension = _fval(row, "bphigh_crudeprev")
        obesity = _fval(row, "obesity_crudeprev")
        chd = _fval(row, "chd_crudeprev")
        copd = _fval(row, "copd_crudeprev")
        stroke = _fval(row, "stroke_crudeprev")

        # Weighted burden score in percentage-like units (0-100).
        weights = [
            (diabetes, 0.24),
            (hypertension, 0.24),
            (obesity, 0.20),
            (chd, 0.14),
            (copd, 0.10),
            (stroke, 0.08),
        ]
        numerator = sum((v or 0.0) * w for v, w in weights)
        denom = sum(w for v, w in weights if v is not None)
        burden = round(numerator / denom, 1) if denom > 0 else None

        total_population = _ival(row, "totalpopulation")
        estimated_patients = None
        if burden is not None and total_population is not None:
            estimated_patients = max(0, int(round(total_population * burden / 100.0)))

        return {
            "chronic_data_year": None,
            "diabetes_prevalence_pct": diabetes,
            "hypertension_prevalence_pct": hypertension,
            "obesity_prevalence_pct": obesity,
            "chd_prevalence_pct": chd,
            "copd_prevalence_pct": copd,
            "stroke_prevalence_pct": stroke,
            "chronic_burden_score": burden,
            "estimated_chronic_patients": estimated_patients,
        }
    except Exception as exc:
        logger.warning("CDC PLACES fetch failed for ZIP %s: %s", zip_code, exc)
        return None
