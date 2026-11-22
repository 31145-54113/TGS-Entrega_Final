"""Tests de hash y verificación de contraseñas."""
import pytest

from app.security.passwords import hash_password, verify_password


def test_hash_formato_autocontenido():
    h = hash_password("hola1234")
    partes = h.split("$")
    assert len(partes) == 4
    assert partes[0] == "pbkdf2_sha256"
    assert partes[1] == "600000"


def test_hash_no_guarda_la_password():
    h = hash_password("hola1234")
    assert "hola1234" not in h


def test_dos_hashes_del_mismo_password_son_distintos():
    """Salt aleatorio: mismo input, distintos hashes."""
    assert hash_password("hola1234") != hash_password("hola1234")


def test_verify_correcto():
    h = hash_password("hola1234")
    assert verify_password("hola1234", h) is True


def test_verify_incorrecto():
    h = hash_password("hola1234")
    assert verify_password("otra", h) is False


def test_verify_hash_corrupto_devuelve_false():
    assert verify_password("hola1234", "basura") is False
    assert verify_password("hola1234", "pbkdf2_sha256$x$y$z") is False
    assert verify_password("hola1234", "otro_algoritmo$1$a$b") is False


def test_hash_rechaza_vacio():
    with pytest.raises(ValueError):
        hash_password("")
