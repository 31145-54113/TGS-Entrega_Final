"""Tests de emisión y validación de JWT."""
import pytest

from app.security.tokens import (
    TokenInvalido,
    create_access_token,
    decode_token,
    get_subject,
)


def test_roundtrip():
    tk = create_access_token(42)
    payload = decode_token(tk)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload and "iat" in payload


def test_get_subject():
    tk = create_access_token(7)
    assert get_subject(decode_token(tk)) == 7


def test_token_manipulado():
    tk = create_access_token(42)
    # Cambiar el último carácter invalida la firma
    with pytest.raises(TokenInvalido):
        decode_token(tk[:-1] + ("a" if tk[-1] != "a" else "b"))


def test_token_basura():
    with pytest.raises(TokenInvalido):
        decode_token("no-es-un-jwt")


def test_token_expirado():
    tk = create_access_token(1, expires_minutes=-1)
    with pytest.raises(TokenInvalido):
        decode_token(tk)


def test_token_sin_sub():
    import jwt
    from app.config import settings

    payload = {"exp": 9999999999, "type": "access"}  # sin "sub"
    tk = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenInvalido):
        decode_token(tk)
