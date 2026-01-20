# CRM Seguimiento Clientes (Backend)

Backend **FastAPI + SQLAlchemy** con UI básica (Jinja2) para seguimiento de cuentas, contactos, oportunidades y dashboard.

## Arranque rápido (Windows)

1. Instala **Python 3.8+** (mejor 3.10/3.11) y marca *Add Python to PATH*.
2. En la carpeta del proyecto, ejecuta:

```bat
START_CRM.bat
```

Esto:
- crea `venv/` si no existe
- instala dependencias desde `requirements.txt`
- arranca el servidor en `http://localhost:8000`

Para parar el servidor:

```bat
scripts\STOP_CRM.bat
```

## Estructura

- `app/` código de la aplicación
- `data/` datos runtime (subidas / backups) — se crea automáticamente
- `logs/` logs runtime — se crea automáticamente
- `scripts/` utilidades (stop / legacy)
- `docs/` documentación (y legacy)

## Configuración

- Copia `.env.example` a `.env` y rellena los valores necesarios.
- **No subas** `.env` a repositorios.

## Notas de limpieza

En este repositorio “limpio” se han excluido intencionadamente:
- `venv/`
- `__pycache__/`, `*.pyc`
- `crm.db` (BD local)
- contenidos de `logs/` y `data/` (runtime)

