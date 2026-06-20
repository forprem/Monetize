from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.adapters.contracts import ApiPrincipal, AuthUser
from app.core.settings import settings


@dataclass
class SessionIdentity:
    email: str
    tenant_id: str
    plan: str
    status: str = "active"
    expires_at: datetime | None = None


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def issue_access_token(user: AuthUser) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.auth_session_ttl_seconds)
    payload = {
        "sub": user.email,
        "tenant_id": user.tenant_id,
        "plan": user.plan,
        "status": user.status,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    payload_b64 = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(
        settings.auth_session_secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{sig}"


def principal_from_access_token(token: str) -> ApiPrincipal | None:
    identity = identity_from_access_token(token)
    if identity is None:
        return None
    return ApiPrincipal(
        api_key=f"session:{identity.email}",
        tenant_id=identity.tenant_id,
        plan=identity.plan,
        status=identity.status,
        expires_at=identity.expires_at,
    )


def identity_from_access_token(token: str) -> SessionIdentity | None:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    expected_sig = hmac.new(
        settings.auth_session_secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        return None

    try:
        payload = json.loads(_urlsafe_b64decode(payload_b64).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int):
        return None
    if datetime.now(timezone.utc).timestamp() >= exp:
        return None

    tenant_id = payload.get("tenant_id")
    plan = payload.get("plan")
    email = payload.get("sub")
    status = payload.get("status", "active")
    if not isinstance(email, str) or not isinstance(tenant_id, str) or not isinstance(plan, str) or status != "active":
        return None

    return SessionIdentity(
        email=email,
        tenant_id=tenant_id,
        plan=plan,
        status=status,
        expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
    )
