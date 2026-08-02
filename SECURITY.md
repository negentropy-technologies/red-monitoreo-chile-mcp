# Politica de seguridad

## Alcance

Este repo contiene `cli.py`, un CLI standalone que guarda localmente
(encriptado con Fernet, clave en el keyring del sistema operativo) el
CORREO/API_KEY que cada usuario registra en climatologia.meteochile.gob.cl
(DMC), y una Skill opcional de Claude Code que lo invoca como comando
de shell. No incluye ningun secreto de Negentropy ni codigo del
servidor MCP en si.

Garantias de diseno vigentes:

- El CORREO/API_KEY nunca sale de la maquina del usuario: `cli.py`
  pega directo contra la API publica de la DMC, sin pasar por ningun
  servidor de Negentropy.
- El secreto nunca pasa por el contexto de un modelo de lenguaje: el
  registro (`register`) se corre a mano en la propia terminal del
  usuario, nunca mediado por un agente/tool-call.
- La encriptacion es reversible (Fernet), nunca hash -- es necesaria
  para reenviar la credencial en claro a la DMC, no para verificarla.

## Reportar una vulnerabilidad

Si encontras un problema de seguridad (por ejemplo, una forma de que
el secreto quede expuesto en disco sin encriptar, en logs, o en el
contexto de un agente), reportalo en privado a
**christian.chacon@negentropy.cl** en vez de abrir un issue
publico. Respondemos en un plazo razonable y coordinamos la
divulgacion una vez resuelto.

No hay programa de recompensas (bug bounty) para este repo.
