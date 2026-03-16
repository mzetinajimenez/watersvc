"""JWT creation and decoding for watersvc access tokens."""

from datetime import datetime, timedelta, timezone

import jwt as pyjwt

from watersvc.config import Settings


def create_access_token(
    user_id: str,
    email: str | None,
    provider: str,
    settings: Settings,
) -> str:
    """Create an HS256-signed JWT access token."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "provider": provider,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expiry_hours),
    }
    return pyjwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> dict:
    """Decode and verify an HS256-signed JWT access token.

    Returns:
        dict with claims: sub, email, provider, iat, exp

    Raises:
        jwt.ExpiredSignatureError: if the token has expired
        jwt.InvalidTokenError: if the token is otherwise invalid
    """
    return pyjwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"])
