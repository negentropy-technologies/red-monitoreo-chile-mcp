# Contribuir

Gracias por el interes. Este repo es chico y de alcance acotado
(el CLI de credenciales DMC + la Skill de Claude Code), asi que las
contribuciones mas utiles son:

- Reportar cuando `cli.py` deje de funcionar contra la API de la DMC.
- Ajustes a la Skill (`.claude/skills/red-monitoreo-chile/SKILL.md`)
  para otros agentes/clientes MCP.
- Mejoras a la documentacion de conexion (`README.md`).

## Como correr los tests

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/ -v
```

Los tests son planos (`assert`, sin fixtures pesadas), corren contra un
keyring falso en memoria -- nunca tocan el keyring real del sistema ni
hacen requests HTTP reales.

## Reglas

- No agregues nada que envie el CORREO/API_KEY del usuario a ningun
  lado que no sea la API oficial de la DMC.
- No agregues nada que permita que el secreto pase por el contexto de
  un modelo de lenguaje (ver `SECURITY.md`).
- Commits: una linea, `tipo: descripcion` (`feat`, `fix`, `docs`, etc).
- Antes de un PR, correr los tests y confirmar que pasan.

Para vulnerabilidades de seguridad, no abras un issue publico: ver
`SECURITY.md`.