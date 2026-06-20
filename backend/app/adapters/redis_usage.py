from __future__ import annotations

from datetime import datetime, timezone

from redis import Redis

from app.adapters.contracts import UsageStore


def _month_bucket(now: datetime) -> str:
    return now.strftime("%Y-%m")


def _seconds_until_next_month(now: datetime) -> int:
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((next_month - now).total_seconds()))


class RedisUsageStore(UsageStore):
    def __init__(self, redis_url: str, client: Redis | None = None) -> None:
        self.client = client or Redis.from_url(redis_url, decode_responses=True)

    def _request_key(self, tenant_id: str, now: datetime) -> str:
        return f"usage:{tenant_id}:{_month_bucket(now)}:requests"

    def _export_key(self, tenant_id: str, now: datetime) -> str:
        return f"usage:{tenant_id}:{_month_bucket(now)}:exports"

    def get_usage(self, tenant_id: str) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        monthly_key = self._request_key(tenant_id, now)
        export_key = self._export_key(tenant_id, now)
        requests_this_month = int(self.client.get(monthly_key) or 0)
        exports_this_month = int(self.client.get(export_key) or 0)
        return {
            "requests_this_month": requests_this_month,
            "exports_this_month": exports_this_month,
        }

    def record_request(self, tenant_id: str, endpoint: str) -> None:
        now = datetime.now(timezone.utc)
        ttl = _seconds_until_next_month(now)
        monthly_key = self._request_key(tenant_id, now)
        self.client.incr(monthly_key)
        self.client.expire(monthly_key, ttl)
        if endpoint == "POST /export":
            export_key = self._export_key(tenant_id, now)
            self.client.incr(export_key)
            self.client.expire(export_key, ttl)
