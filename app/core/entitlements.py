from __future__ import annotations

PLAN_PERMISSIONS: dict[str, set[str]] = {
    "trial": {
        "map:read",
        "zip:summary:read",
        "zip:compare:read",
        "usage:read",
    },
    "basic": {
        "map:read",
        "zip:summary:read",
        "zip:compare:read",
        "usage:read",
    },
    "pro": {
        "map:read",
        "zip:summary:read",
        "zip:compare:read",
        "usage:read",
        "export:create",
        "export:read",
    },
    "enterprise": {
        "admin:exports:process-batch",
        "admin:exports:read",
        "admin:exports:fail",
        "admin:exports:process",
        "admin:exports:retry",
        "admin:usage:read",
        "admin:audit:read",
        "admin:api-keys:read",
        "admin:api-keys:rotate",
        "admin:api-keys:write",
        "admin:api-keys:revoke",
        "admin:users:read",
        "admin:users:create",
        "admin:users:disable",
        "admin:users:password",
        "map:read",
        "zip:summary:read",
        "zip:compare:read",
        "usage:read",
        "export:create",
        "export:read",
    },
}


PLAN_LIMITS: dict[str, dict[str, int]] = {
    "trial": {
        "requests_per_month": 2,
        "exports_per_month": 0,
    },
    "basic": {
        "requests_per_month": 5000,
        "exports_per_month": 0,
    },
    "pro": {
        "requests_per_month": 100000,
        "exports_per_month": 200,
    },
    "enterprise": {
        "requests_per_month": 1000000,
        "exports_per_month": 10000,
    },
}
