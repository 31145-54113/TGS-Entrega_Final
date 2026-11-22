"""Hash y verificación de contraseñas con PBKDF2-HMAC-SHA256.

Formato del hash almacenado (autocontenido, sin estado externo):

    pbkdf2_sha256$<iteraciones>$<salt_b64>$<hash_b64>

Incluir el algoritmo y las iteraciones permite migrar a futuro sin
romper los hashes ya guardados.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000          # recomendación OWASP 2024 para SHA256
SALT_BYTES = 16
HASH_BYTES = 32


def _b64encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def hash_password(plain: str) -> str:
    """Devuelve el hash autocontenido de una contraseña en texto plano."""
    if not isinstance(plain, str) or not plain:
        raise ValueError("La contraseña no puede estar vacía")

    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, ITERATIONS, HASH_BYTES)

    return f"{ALGORITHM}${ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(plain: str, stored: str) -> bool:
    """Compara una contraseña en claro contra un hash almacenado.

    Devuelve False (sin lanzar) si el hash almacenado está corrupto o
    mal formado: un dato inválido no debe tumbar el login.
    """
    try:
        algorithm, iterations_s, salt_b64, hash_b64 = stored.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        iterations = int(iterations_s)
        salt = _b64decode(salt_b64)
        expected = _b64decode(hash_b64)
    except (ValueError, TypeError):
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations, len(expected))
    return hmac.compare_digest(candidate, expected)
