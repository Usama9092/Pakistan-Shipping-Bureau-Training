from __future__ import annotations
import os
import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@dataclass(frozen=True)
class SecurityPolicy:
    min_password_length: int = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))
    max_password_length: int = int(os.getenv("MAX_PASSWORD_LENGTH", "128"))
    require_mixed_case: bool = os.getenv("PASSWORD_REQUIRE_MIXED_CASE", "true").lower() == "true"
    require_digit: bool = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
    require_symbol: bool = os.getenv("PASSWORD_REQUIRE_SYMBOL", "true").lower() == "true"

def password_errors(password: str) -> list[str]:
    p = password or ""
    policy = SecurityPolicy()
    errors = []
    if len(p) < policy.min_password_length: errors.append(f"Use at least {policy.min_password_length} characters.")
    if len(p) > policy.max_password_length: errors.append(f"Use no more than {policy.max_password_length} characters.")
    if policy.require_mixed_case and (p.lower() == p or p.upper() == p): errors.append("Use both upper- and lower-case letters.")
    if policy.require_digit and not any(c.isdigit() for c in p): errors.append("Include at least one number.")
    if policy.require_symbol and not any(not c.isalnum() for c in p): errors.append("Include at least one symbol.")
    return errors

def valid_email(value: str) -> bool:
    return bool(EMAIL_RE.fullmatch((value or "").strip()))
