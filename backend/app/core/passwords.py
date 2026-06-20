from __future__ import annotations

import hashlib
import hmac


def hash_password(password: str) -> str:
    # Dev-friendly hash for demo users. Replace with bcrypt/argon2 in production.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), stored_hash)
