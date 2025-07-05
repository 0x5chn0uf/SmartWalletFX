"""Pydantic schemas for JSON Web Key (JWK) and JSON Web Key Set (JWKS).

These models intentionally cover the subset of fields required for RSA
signing keys used by our authentication system ("sig" use, RS256 alg).  The
schema can be extended to support additional key types (EC, OKP, symmetric)
in future tasks.
"""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field, constr, validator

# ---------------------------------------------------------------------------
# Individual JWK schema – supporting RSA public keys ("kty" == "RSA").
# ---------------------------------------------------------------------------


class JWK(BaseModel):
    """JSON Web Key representation (RSA, public, signature use).

    Required fields for RSA public keys according to RFC-7517 / RFC-7518:
    - kty: Key Type – "RSA"
    - use: Public Key Use – "sig" (signature verification)
    - kid: Key ID – unique identifier referenced by JWT *kid* header
    - alg: Algorithm – e.g. "RS256"
    - n:   Modulus – base64url-encoded big-endian unsigned integer
    - e:   Exponent – base64url-encoded big-endian unsigned integer
    """

    kty: Literal["RSA"] = Field(
        "RSA", description="Key Type – always 'RSA' for our keys"
    )
    use: Literal["sig"] = Field(
        "sig", description="Public Key Use – 'sig' for signature"
    )
    kid: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Key identifier"
    )
    alg: Literal["RS256", "RS384", "RS512"] = Field(
        "RS256", description="Signature algorithm"
    )
    n: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Base64url modulus"
    )
    e: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Base64url exponent"
    )

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "kty": "RSA",
                "use": "sig",
                "kid": "abc123",
                "alg": "RS256",
                "n": "0vx7agoebGcQSuuPiLJXZptN27IL...",
                "e": "AQAB",
            }
        }

    # Basic validator: ensure *n* and *e* are base64url (no padding, url-safe)
    @validator("n", "e")
    def _no_padding(cls, v: str) -> str:  # noqa: N805
        if "=" in v:
            raise ValueError(
                "Base64url fields *n* and *e* must not contain '=' padding"
            )
        return v


# ---------------------------------------------------------------------------
# JWK Set – wrapper object holding a list of JWKs as per RFC-7517 §5.  The
# field must be named exactly "keys".
# ---------------------------------------------------------------------------


class JWKSet(BaseModel):
    """JSON Web Key Set – container for one or more JWK objects."""

    keys: List[JWK] = Field(..., description="Array of JWK objects")

    class Config:
        schema_extra = {
            "example": {
                "keys": [
                    {
                        "kty": "RSA",
                        "use": "sig",
                        "kid": "abc123",
                        "alg": "RS256",
                        "n": "0vx7agoebGcQSuuPiLJXZptN27IL...",
                        "e": "AQAB",
                    }
                ]
            }
        }
