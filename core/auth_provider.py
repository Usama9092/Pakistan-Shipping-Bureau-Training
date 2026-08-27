from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class AuthResult:
    ok: bool
    identity_id: str = ""
    email: str = ""
    error: str = ""

class SupabaseAuthProvider:
    """Optional Supabase Auth adapter.

    The service-role key is never used for interactive sign-in. Interactive
    authentication uses the anonymous client key and returns only identity
    metadata to the application layer.
    """
    def __init__(self, url: str, anon_key: str, create_client: Callable[..., Any] | None):
        self.enabled = bool(url and anon_key and create_client)
        self.client = create_client(url, anon_key) if self.enabled else None

    def sign_in(self, email: str, password: str) -> AuthResult:
        if not self.enabled or self.client is None:
            return AuthResult(False, error="Supabase Auth is not configured")
        try:
            response = self.client.auth.sign_in_with_password({"email": email, "password": password})
            user = getattr(response, "user", None)
            if not user:
                return AuthResult(False, error="Authentication failed")
            return AuthResult(True, identity_id=str(getattr(user, "id", "")), email=str(getattr(user, "email", email)))
        except Exception:
            return AuthResult(False, error="Authentication failed")

    def request_password_reset(self, email: str, redirect_to: str | None = None) -> AuthResult:
        if not self.enabled or self.client is None:
            return AuthResult(False, error="Supabase Auth is not configured")
        try:
            kwargs = {"email": email}
            if redirect_to:
                kwargs["options"] = {"redirect_to": redirect_to}
            self.client.auth.reset_password_for_email(**kwargs)
            return AuthResult(True, email=email)
        except Exception:
            return AuthResult(False, error="Password reset request could not be completed")
