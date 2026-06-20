from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_urlsafe

from app.adapters.contracts import ApiPrincipal, AuthStore, AuthUser
from app.core.entitlements import PLAN_PERMISSIONS
from app.core.passwords import hash_password, verify_password
from app.core.settings import settings


class InMemoryAuthStore(AuthStore):
    def __init__(self) -> None:
        self._principals: dict[str, ApiPrincipal] = {
            settings.default_api_key: ApiPrincipal(
                api_key=settings.default_api_key,
                tenant_id=settings.default_tenant_id,
                plan=settings.default_plan,
                status="active",
                expires_at=None,
            ),
            settings.basic_api_key: ApiPrincipal(
                api_key=settings.basic_api_key,
                tenant_id=settings.basic_tenant_id,
                plan="basic",
                status="active",
                expires_at=None,
            ),
            settings.trial_api_key: ApiPrincipal(
                api_key=settings.trial_api_key,
                tenant_id=settings.trial_tenant_id,
                plan="trial",
                status="active",
                expires_at=None,
            ),
            settings.admin_api_key: ApiPrincipal(
                api_key=settings.admin_api_key,
                tenant_id=settings.admin_tenant_id,
                plan="enterprise",
                status="active",
                expires_at=None,
            ),
        }
        self._users: dict[str, dict[str, str]] = {
            "admin@zipintel.local": {
                "password_hash": hash_password("admin123"),
                "tenant_id": settings.admin_tenant_id,
                "plan": "enterprise",
                "status": "active",
            },
            "pro@zipintel.local": {
                "password_hash": hash_password("pro123"),
                "tenant_id": settings.default_tenant_id,
                "plan": settings.default_plan,
                "status": "active",
            },
            "basic@zipintel.local": {
                "password_hash": hash_password("basic123"),
                "tenant_id": settings.basic_tenant_id,
                "plan": "basic",
                "status": "active",
            },
            "trial@zipintel.local": {
                "password_hash": hash_password("trial123"),
                "tenant_id": settings.trial_tenant_id,
                "plan": "trial",
                "status": "active",
            },
        }

    def get_principal(self, api_key: str) -> ApiPrincipal | None:
        principal = self._principals.get(api_key)
        if principal is None or principal.status != "active":
            return None
        if principal.expires_at is not None and principal.expires_at <= datetime.now(timezone.utc):
            return None
        return principal

    def is_allowed(self, principal: ApiPrincipal, action: str) -> bool:
        allowed = PLAN_PERMISSIONS.get(principal.plan, set())
        return action in allowed

    def create_api_key(
        self,
        tenant_id: str,
        plan: str,
        expires_at: datetime | None = None,
    ) -> ApiPrincipal:
        api_key = f"live_{token_urlsafe(18)}"
        principal = ApiPrincipal(
            api_key=api_key,
            tenant_id=tenant_id,
            plan=plan,
            status="active",
            expires_at=expires_at,
        )
        self._principals[api_key] = principal
        return principal

    def list_api_keys(self, tenant_id: str | None = None) -> list[ApiPrincipal]:
        principals = list(self._principals.values())
        if tenant_id is not None:
            principals = [principal for principal in principals if principal.tenant_id == tenant_id]
        return principals

    def revoke_api_key(self, api_key: str) -> ApiPrincipal | None:
        principal = self._principals.get(api_key)
        if principal is None:
            return None
        principal.status = "revoked"
        return principal

    def rotate_api_key(self, api_key: str, expires_at: datetime | None = None) -> ApiPrincipal | None:
        principal = self._principals.get(api_key)
        if principal is None:
            return None
        principal.status = "revoked"
        return self.create_api_key(
            tenant_id=principal.tenant_id,
            plan=principal.plan,
            expires_at=principal.expires_at if expires_at is None else expires_at,
        )

    def authenticate_user(self, email: str, password: str) -> AuthUser | None:
        key = email.lower().strip()
        user = self._users.get(key)
        if user is None:
            return None
        if user["status"] != "active":
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return AuthUser(
            email=key,
            tenant_id=user["tenant_id"],
            plan=user["plan"],
            status=user["status"],
        )

    def list_users(self, tenant_id: str | None = None) -> list[AuthUser]:
        items: list[AuthUser] = []
        for email, user in self._users.items():
            if tenant_id is not None and user["tenant_id"] != tenant_id:
                continue
            items.append(
                AuthUser(
                    email=email,
                    tenant_id=user["tenant_id"],
                    plan=user["plan"],
                    status=user["status"],
                )
            )
        return sorted(items, key=lambda item: (item.tenant_id, item.email))

    def create_user(self, email: str, password: str, tenant_id: str, plan: str) -> AuthUser:
        key = email.lower().strip()
        if key in self._users:
            raise ValueError("User already exists")
        self._users[key] = {
            "password_hash": hash_password(password),
            "tenant_id": tenant_id,
            "plan": plan,
            "status": "active",
        }
        return AuthUser(email=key, tenant_id=tenant_id, plan=plan, status="active")

    def disable_user(self, email: str) -> AuthUser | None:
        key = email.lower().strip()
        user = self._users.get(key)
        if user is None:
            return None
        user["status"] = "disabled"
        return AuthUser(
            email=key,
            tenant_id=user["tenant_id"],
            plan=user["plan"],
            status=user["status"],
        )

    def set_user_password(self, email: str, password: str) -> AuthUser | None:
        key = email.lower().strip()
        user = self._users.get(key)
        if user is None:
            return None
        user["password_hash"] = hash_password(password)
        return AuthUser(
            email=key,
            tenant_id=user["tenant_id"],
            plan=user["plan"],
            status=user["status"],
        )
