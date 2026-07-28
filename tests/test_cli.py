"""
Tests planos para cli.py. Solo prueba _fernet()/register()/
_load_credenciales() de punta a punta contra un keyring falso en
memoria (monkeypatch): nunca toca el keyring real del SO ni hace un
request HTTP de verdad.
"""

import pytest

import cli


class _FakeKeyring:
    def __init__(self):
        self._store = {}

    def get_password(self, service, key):
        return self._store.get((service, key))

    def set_password(self, service, key, value):
        self._store[(service, key)] = value


@pytest.fixture
def fake_keyring(monkeypatch, tmp_path):
    fake = _FakeKeyring()
    monkeypatch.setattr(cli, "keyring", fake)
    monkeypatch.setattr(cli, "FALLBACK_PATH", tmp_path / "dmc_credenciales.enc")
    return fake


def test_register_y_load_hacen_roundtrip(monkeypatch, fake_keyring):
    respuestas = iter(["usuario@ejemplo.cl"])
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))
    monkeypatch.setattr(cli.getpass, "getpass", lambda _: "clave-secreta")

    cli.register()
    config = cli._load_credenciales()

    assert config == {"correo": "usuario@ejemplo.cl", "api_key": "clave-secreta"}


def test_register_rechaza_campos_vacios(monkeypatch, fake_keyring):
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(cli.getpass, "getpass", lambda _: "")
    with pytest.raises(SystemExit):
        cli.register()
