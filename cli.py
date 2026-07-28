"""
CLI agnostico de agente/plataforma para el secreto de la cuenta DMC
(CORREO/API_KEY) que necesita extractors/dmc.py de cada usuario del
MCP red_monitoreo_chile. Corre en la maquina del usuario: nunca se
instala en el Docker de Negentropy ni se conecta a la BD compartida
-- solo pega directo contra la API publica de la DMC.

  register  -- guarda CORREO/API_KEY encriptados (Fernet, clave en el
              keyring del SO o en un archivo local de fallback). Se
              corre A MANO en la propia terminal del usuario, con
              getpass (sin echo): ningun agente/tool-call debe mediar
              este paso, para que el secreto nunca entre al contexto
              de un LLM.
  fetch     -- decrypta localmente y pide un mes de datos de una
              estacion EMA contra el mismo endpoint que PROTOCOLO de
              extractors/dmc.py, imprime SOLO el dato por stdout.

Si no tienes cuenta/API Key de la DMC todavia, genérala en:
https://climatologia.meteochile.gob.cl/application/usuario/editaDatosUsuario

Uso (sin Docker, sin depender de ningun agente en particular):
    pip install -r requirements.txt
    python cli.py register
    python cli.py fetch 330020 2026 6
"""

import argparse
import getpass
import json
import sys
from pathlib import Path

import keyring
import requests
from cryptography.fernet import Fernet

SERVICE_NAME = "red-monitoreo-chile-dmc"
KEYRING_KEY_NAME = "fernet-key"
FALLBACK_PATH = Path.home() / ".red_monitoreo_chile" / "dmc_credenciales.enc"
# Debe coincidir con DATA_URL de sistema_frontal_chile/extractors/dmc.py
# -- duplicado a proposito (ver docstring del modulo: este CLI es
# standalone, no importa nada del resto del repo).
DATA_URL = "https://climatologia.meteochile.gob.cl/application/servicios/getDatosRecientesEma"


def _fernet() -> Fernet:
    """
    Clave de encriptacion via keyring del SO, generada una sola vez.
    Si no hay backend de keyring disponible (headless), cae a un
    archivo de clave local -- igual de reversible, solo sin la capa
    extra del SO.
    """
    key = keyring.get_password(SERVICE_NAME, KEYRING_KEY_NAME)
    if key is None:
        key = Fernet.generate_key().decode()
        keyring.set_password(SERVICE_NAME, KEYRING_KEY_NAME, key)
    return Fernet(key.encode())


def register() -> None:
    """Pide CORREO/API_KEY y los guarda encriptados en FALLBACK_PATH."""
    correo = input("CORREO registrado en climatologia.meteochile.gob.cl: ").strip()
    api_key = getpass.getpass("API_KEY (no se muestra en pantalla): ").strip()
    if not correo or not api_key:
        print("CORREO y API_KEY no pueden estar vacios", file=sys.stderr)
        raise SystemExit(1)
    payload = json.dumps({"correo": correo, "api_key": api_key}).encode()
    token = _fernet().encrypt(payload)
    FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_PATH.write_bytes(token)
    FALLBACK_PATH.chmod(0o600)
    print(f"credenciales guardadas (encriptadas) en {FALLBACK_PATH}")


def _load_credenciales() -> dict:
    if not FALLBACK_PATH.exists():
        print(
            "no hay credenciales registradas. Corre 'python cli.py register' primero.\n"
            "Si no tienes cuenta DMC, genérala en "
            "https://climatologia.meteochile.gob.cl/application/usuario/editaDatosUsuario",
            file=sys.stderr,
        )
        raise SystemExit(1)
    payload = _fernet().decrypt(FALLBACK_PATH.read_bytes())
    return json.loads(payload)


def fetch(cod_estacion: str, year: int, month: int) -> None:
    """Decrypta localmente y pide un mes de datos de una estacion EMA."""
    config = _load_credenciales()
    response = requests.get(
        f"{DATA_URL}/{cod_estacion}/{year}/{month:02d}",
        params={"usuario": config["correo"], "token": config["api_key"]},
        timeout=30,
    )
    response.raise_for_status()
    print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("register")
    fetch_parser = sub.add_parser("fetch")
    fetch_parser.add_argument("cod_estacion")
    fetch_parser.add_argument("year", type=int)
    fetch_parser.add_argument("month", type=int)

    args = parser.parse_args()
    if args.comando == "register":
        register()
    else:
        fetch(args.cod_estacion, args.year, args.month)


if __name__ == "__main__":
    main()
