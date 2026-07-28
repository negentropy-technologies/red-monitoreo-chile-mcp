# MCP Red de Monitoreo de Chile 

[![tests](https://img.shields.io/github/actions/workflow/status/negentropy-technologies/red-monitoreo-chile-mcp/tests.yml?branch=master&label=tests)](https://github.com/negentropy-technologies/red-monitoreo-chile-mcp/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.12-blue.svg)](requirements.txt)

MCP remoto (FastMCP, streamable HTTP, OAuth via GitHub) que centraliza el
catalogo de estaciones de tres redes de monitoreo de Chile -- DGA (red
hidrometrica nacional), EMA de la DMC, EMA del INIA Agromet -- con
geometria y el protocolo de extraccion de cada fuente.

```
https://api.negentropytechnologies.com/mcp/red-monitoreo-chile/
```

Este MCP es puente y contexto, no fuente de datos: NUNCA sirve datos de
monitoreo (series/lecturas) desde la base de Negentropy. La unica
consulta en vivo es el catalogo de estaciones (cuales existen, su
geometria y metadata). Para datos reales, es el agente o el usuario
quien ejecuta la extraccion contra la fuente original, siguiendo el
`protocolo` que cada respuesta ya trae.

Protocolo abierto: funciona igual en Claude Code, Claude Desktop,
Antigravity, Codex, o cualquier otro cliente MCP.

## Conectar tu cliente

### Claude Code

```bash
claude mcp add --transport http red-monitoreo-chile https://api.negentropytechnologies.com/mcp/red-monitoreo-chile/
```

Despues, `/mcp` dentro de Claude Code te lleva al login con GitHub.

### Claude Desktop

Configuracion -> Conectores -> Agregar conector personalizado, con la
misma URL. Soporta OAuth de forma nativa, sin pasos extra. No uses
`claude_desktop_config.json` para esto: Claude Desktop ignora ahi los
servidores remotos.

### Antigravity (CLI e IDE, comparten config)

```json
{
  "mcpServers": {
    "red-monitoreo-chile": {
      "serverUrl": "https://api.negentropytechnologies.com/mcp/red-monitoreo-chile/"
    }
  }
}
```

en `~/.gemini/config/mcp_config.json` (o `.agents/mcp_config.json` por
proyecto). Antigravity todavia no soporta el spec de OAuth de MCP de
forma confiable -- si el login desde el panel `/mcp` no se completa,
usa en su lugar el puente `mcp-remote` (hace el login de forma
automatica, en un navegador, una sola vez):

```json
{
  "mcpServers": {
    "red-monitoreo-chile": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://api.negentropytechnologies.com/mcp/red-monitoreo-chile/"]
    }
  }
}
```

### Codex CLI

```bash
codex mcp add red-monitoreo-chile --url https://api.negentropytechnologies.com/mcp/red-monitoreo-chile/ --oauth-resource https://api.negentropytechnologies.com/mcp/red-monitoreo-chile/
codex mcp login red-monitoreo-chile
```

Requiere una version de Codex que soporte `--oauth-resource`. No uses
la app de escritorio de Codex ni la extension de VS Code para este
servidor todavia: hay un bug conocido y abierto en Codex
(`openai/codex#6465`, `#7820`) donde no leen los servidores MCP
definidos en `~/.codex/config.toml`, aunque `codex mcp list` los
muestre bien. Usa la CLI desde terminal hasta que se resuelva.

## Herramientas del MCP

`get_red_monitoreo(fuente, bbox=None, region=None, comuna_id=None,
cuenca_id=None, subcuenca_id=None, subsubcuenca_id=None, insular=None)`
-- catalogo de estaciones (`fuente` es `dga`, `agromet` o `dmc`), mas
el `protocolo` de esa fuente. Sin filtros devuelve la red completa. Los
filtros geograficos se combinan entre si; `insular` es excluyente con
el resto.

`get_variables_medidas(fuente, cod_estacion=None)` -- que variables
mide una fuente (o una estacion puntual): metadata de capacidad, nunca
el valor de una lectura real.

## Extraer datos reales: una por fuente

El campo `protocolo` de `get_red_monitoreo` trae el mecanismo exacto
(endpoints, flujo, notas) de cada fuente. Resumen:

- **DGA**: web scraping con sesion (cookie `JSESSIONID`), sin cuenta.
  Requiere User-Agent de navegador (el WAF bloquea librerias) y pacing
  entre requests. Sus servidores tienen latencia alta: extraer muchas
  estaciones de una sola vez es lento y poco confiable -- para uso a
  escala conviene un pipeline propio (con reintentos y pacing), no
  scraping ad-hoc estacion por estacion.
- **Agromet (INIA)**: endpoint interno bloqueado por WAF de
  User-Agent/rafagas -- igual que DGA necesita User-Agent de navegador
  y pacing (1s entre estaciones), pero se extrae mas facil que DGA una
  vez resuelto el WAF.
- **DMC**: API REST con cuenta propia del usuario (nunca de
  Negentropy) -- la mas facil de extraer una vez que se cuenta con el
  CORREO/API_KEY. Ver la seccion siguiente.

## Condiciones de uso

`red_monitoreo_chile` no es un producto oficial de la DGA, la DMC, el
INIA ni el MOP, no tiene afiliacion con ellos, y no garantiza
disponibilidad, exactitud ni estabilidad de sus portales -- son
servicios publicos de terceros, fuera del control de Negentropy. Quien
use este MCP y/o el CLI de credenciales de este repo acepta que la
extraccion real de datos es su propia responsabilidad, sujeta a los
terminos de uso de cada portal de origen.

### Comportamiento real por fuente (verificado en vivo, 2026-07-28)

Medido desde el entorno de este agente con `curl`, User-Agent de
navegador, sin replicar sesion/cookies/TLS fingerprint completo de un
navegador real (el peor caso -- no el flujo que ya implementan
`extractors/dga.py`/`agromet.py` en el repo principal, que si maneja
sesion/cookies):

- **DGA** (`snia.mop.gob.cl`): la conexion TCP se establece rapido
  (~0.1-0.3s), pero el servidor no devuelve ninguna respuesta HTTP
  dentro de 30s por request (2/2 intentos). Consistente con el WAF: sin
  la sesion (cookie `JSESSIONID`) y el flujo exacto que espera el
  portal, la conexion simplemente cuelga en vez de responder rapido con
  un error. Extraer muchas estaciones de una sola vez con reintentos
  ingenuos puede tardar minutos y saturar el portal.
- **Agromet** (`agromet.cl`): la conexion TLS falla antes de llegar a
  HTTP porque el servidor no envia su certificado intermedio (ZeroSSL)
  en el handshake -- ya resuelto en `extractors/agromet.py`
  (completa la cadena manualmente en vez de desactivar la verificacion
  TLS). Ademas exige User-Agent de navegador y pacing de 1s entre
  estaciones.
- **DMC** (`climatologia.meteochile.gob.cl`): unica con API REST
  estable y cuenta propia. Su portal publico respondio con latencia
  normal (~1.4s) en esta misma prueba.

Control de referencia: un host generico y rapido (`api.github.com`)
respondio en ~0.5s desde el mismo entorno -- descarta que la demora de
DGA sea un problema de red local.

No es una medicion exhaustiva ni un SLA: el comportamiento de estos
portales de terceros puede cambiar sin aviso, y fue un puñado de
requests puntuales, no una serie estadistica. Tampoco se extrajo
ningun dato real de monitoreo en esta prueba -- los requests a
DGA/Agromet fallaron antes de recibir contenido, y ninguno paso por el
MCP (corrieron fuera de el, como diagnostico de red).

### Responsabilidad

Negentropy no es responsable por bloqueos, rate limiting, cambios de
API, o caidas de los portales de DGA/MOP, Agromet/INIA o DMC. Este
repo (CLI + skill) se entrega "tal cual", sin garantia, segun la
licencia MIT (`LICENSE`).

## Credenciales DMC

Unica fuente que exige cuenta real (`CORREO`/`API_KEY` de
`climatologia.meteochile.gob.cl`). Se maneja con el `cli.py` de este
mismo directorio: un CLI agnostico de agente/plataforma, standalone
(no depende de nada del resto del repo de Negentropy).

Si no se tiene cuenta/API Key todavia, se puede generar en:
https://climatologia.meteochile.gob.cl/application/usuario/editaDatosUsuario

```bash
pip install -r requirements.txt
python cli.py register   # ejecutar esto en tu propia terminal, nunca a traves de un agente
python cli.py fetch <cod_estacion> <year> <month>
```

`register` guarda tu CORREO/API_KEY encriptados (Fernet) en
`~/.red_monitoreo_chile/dmc_credenciales.enc`, usando el keyring de tu
sistema operativo para la clave de encriptacion (o un archivo local si
tu sistema no tiene keyring). `fetch` decrypta localmente y solo
imprime el dato de la DMC por stdout -- tu credencial nunca sale de tu
maquina ni pasa por ningun modelo de lenguaje.

### Uso con un agente (Claude Code, Antigravity, Codex, etc.)

Pídele siempre al agente que llame a `python cli.py fetch ...` como un
comando de shell (nunca escribir el CORREO/API_KEY en el chat para que
el agente los use). Si usas Claude Code,
`.claude/skills/red-monitoreo-chile/SKILL.md` es una capa opcional de
conveniencia que hace exactamente eso -- si clonas o copias este repo
dentro del tuyo, Claude Code la detecta sola; si no, cópiala a mano a
tu carpeta de skills. No es necesaria para usar este CLI.

## Por que confiar en esto

- El MCP nunca pide ni ve tu CORREO/API_KEY de DMC -- vive encriptado
  solo en tu maquina.
- El MCP nunca sirve datos de monitoreo desde la base de Negentropy,
  solo catalogo de estaciones y protocolo de extraccion.
- Todo el codigo de este directorio (`cli.py`, esta skill) es publico y
  auditable -- no depende de ningun secreto de Negentropy para
  funcionar.

## Licencia, seguridad y contribuciones

Este repo se distribuye bajo licencia MIT (ver `LICENSE`). Para
reportar una vulnerabilidad ver `SECURITY.md`; para contribuir, ver
`CONTRIBUTING.md`. Rige el `CODE_OF_CONDUCT.md` (Contributor Covenant).
