"""Verify identity tokens from Apple and Google sign-in providers."""

import time

import jwt
from jwt import PyJWKClient

from watersvc.config import Settings

# Module-level JWKS cache: {url: (PyJWKClient, fetch_time)}
_jwks_cache: dict[str, tuple[PyJWKClient, float]] = {}
_CACHE_TTL = 3600  # 1 hour

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUER = "https://accounts.google.com"


def _get_jwks_client(url: str) -> PyJWKClient:
    """Get or create a cached JWKS client for the given URL."""
    now = time.time()
    if url in _jwks_cache:
        client, fetched_at = _jwks_cache[url]
        if now - fetched_at < _CACHE_TTL:
            return client
    client = PyJWKClient(url)
    _jwks_cache[url] = (client, now)
    return client


async def verify_apple_token(identity_token: str, settings: Settings) -> dict:
    """Verify an Apple identity token and return claims.

    Returns:
        dict with keys: sub, email, email_verified
    """
    jwks_client = _get_jwks_client(APPLE_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(identity_token)

    payload = jwt.decode(
        identity_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.apple_bundle_id,
        issuer=APPLE_ISSUER,
    )
    return {
        "sub": payload["sub"],
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", False),
    }


async def verify_google_token(id_token: str, settings: Settings) -> dict:
    """Verify a Google ID token and return claims.

    Returns:
        dict with keys: sub, email, email_verified
    """
    jwks_client = _get_jwks_client(GOOGLE_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)

    payload = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.google_client_id,
        issuer=GOOGLE_ISSUER,
    )
    return {
        "sub": payload["sub"],
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", False),
    }
